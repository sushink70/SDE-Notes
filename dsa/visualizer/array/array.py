#!/usr/bin/env python3
"""
Elite Array & Sorting Algorithm Visualizer
Master sorting through step-by-step visualization.

Usage:
    python sort_viz.py
    
Features:
- ASCII bar chart visualization
- Step-by-step algorithm animation
- Comparison and swap tracking
- Multiple sorting algorithms
- Time/space complexity analysis
- Interactive exploration mode
"""

from typing import List, Tuple, Optional, Callable
import time
import sys
import os
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


class State(Enum):
    """Visual states for array elements."""
    NORMAL = 0
    COMPARING = 1
    SWAPPING = 2
    SORTED = 3
    PIVOT = 4
    MINIMUM = 5


@dataclass
class VisualizerStats:
    """Track algorithm performance metrics."""
    comparisons: int = 0
    swaps: int = 0
    array_accesses: int = 0
    recursive_calls: int = 0


class ArrayVisualizer:
    """
    Elite visualization engine for arrays and sorting algorithms.
    Supports multiple rendering styles and interactive exploration.
    """
    
    def __init__(self, arr: List[int], delay: float = 0.3):
        self.original_arr = arr.copy()
        self.arr = arr.copy()
        self.delay = delay
        self.states = [State.NORMAL] * len(arr)
        self.stats = VisualizerStats()
        self.algorithm_name = ""
        
    # ==================== CORE VISUALIZATION ====================
    
    def display(self, title: Optional[str] = None, show_stats: bool = True) -> None:
        """Main display function with bar chart and array view."""
        self._clear_screen()
        
        print("=" * 80)
        if title:
            print(f"🎯 {title}")
        print("=" * 80)
        
        # Bar chart visualization
        self._display_bars()
        
        # Array representation with indices
        self._display_array()
        
        # Statistics
        if show_stats:
            self._display_stats()
        
        print("=" * 80)
        time.sleep(self.delay)
    
    def _display_bars(self) -> None:
        """Display array as horizontal bar chart with colors."""
        if not self.arr:
            return
        
        max_val = max(self.arr)
        bar_width = 50  # Max width of bars
        
        for i, val in enumerate(self.arr):
            # Calculate bar length
            bar_len = int((val / max_val) * bar_width) if max_val > 0 else 0
            
            # Choose color based on state
            color = self._get_color(self.states[i])
            state_symbol = self._get_state_symbol(self.states[i])
            
            # Build bar
            bar = "█" * bar_len
            
            # Display with value and state
            print(f"{i:2d} │ {color}{bar}{Color.RESET} {val:3d} {state_symbol}")
    
    def _display_array(self) -> None:
        """Display array in compact format with colors."""
        print("\n📊 Array: [", end="")
        for i, val in enumerate(self.arr):
            color = self._get_color(self.states[i])
            if i > 0:
                print(", ", end="")
            print(f"{color}{val:3d}{Color.RESET}", end="")
        print("]")
    
    def _display_stats(self) -> None:
        """Display algorithm performance metrics."""
        print(f"\n📈 Statistics:")
        print(f"   Comparisons: {self.stats.comparisons}")
        print(f"   Swaps: {self.stats.swaps}")
        print(f"   Array Accesses: {self.stats.array_accesses}")
        if self.stats.recursive_calls > 0:
            print(f"   Recursive Calls: {self.stats.recursive_calls}")
    
    def _get_color(self, state: State) -> str:
        """Map state to color."""
        color_map = {
            State.NORMAL: Color.WHITE,
            State.COMPARING: Color.YELLOW,
            State.SWAPPING: Color.RED,
            State.SORTED: Color.GREEN,
            State.PIVOT: Color.MAGENTA,
            State.MINIMUM: Color.CYAN,
        }
        return color_map.get(state, Color.WHITE)
    
    def _get_state_symbol(self, state: State) -> str:
        """Map state to symbol."""
        symbol_map = {
            State.NORMAL: "",
            State.COMPARING: "👀",
            State.SWAPPING: "🔄",
            State.SORTED: "✓",
            State.PIVOT: "🎯",
            State.MINIMUM: "⭐",
        }
        return symbol_map.get(state, "")
    
    def _clear_screen(self) -> None:
        """Clear terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def _reset_states(self) -> None:
        """Reset all states to normal."""
        self.states = [State.NORMAL] * len(self.arr)
    
    def _compare(self, i: int, j: int) -> bool:
        """Compare two elements with visualization."""
        self.stats.comparisons += 1
        self.stats.array_accesses += 2
        self._reset_states()
        self.states[i] = State.COMPARING
        self.states[j] = State.COMPARING
        self.display(f"{self.algorithm_name} - Comparing indices {i} and {j}")
        return self.arr[i] > self.arr[j]
    
    def _swap(self, i: int, j: int) -> None:
        """Swap two elements with visualization."""
        self.stats.swaps += 1
        self.stats.array_accesses += 4  # 2 reads + 2 writes
        self._reset_states()
        self.states[i] = State.SWAPPING
        self.states[j] = State.SWAPPING
        self.display(f"{self.algorithm_name} - Swapping indices {i} and {j}")
        self.arr[i], self.arr[j] = self.arr[j], self.arr[i]
    
    def _mark_sorted(self, start: int, end: int) -> None:
        """Mark range as sorted."""
        for i in range(start, end + 1):
            if 0 <= i < len(self.arr):
                self.states[i] = State.SORTED
    
    # ==================== SORTING ALGORITHMS ====================
    
    def bubble_sort(self) -> None:
        """
        Bubble Sort: Repeatedly swap adjacent elements if out of order.
        Time: O(n²) worst/avg, O(n) best
        Space: O(1)
        Stable: Yes
        """
        self.algorithm_name = "Bubble Sort"
        n = len(self.arr)
        
        for i in range(n):
            swapped = False
            
            for j in range(0, n - i - 1):
                if self._compare(j, j + 1):
                    self._swap(j, j + 1)
                    swapped = True
            
            # Mark last element as sorted
            self._mark_sorted(n - i - 1, n - 1)
            
            # Early termination if no swaps
            if not swapped:
                break
        
        self._reset_states()
        self._mark_sorted(0, n - 1)
        self.display(f"{self.algorithm_name} - Complete!")
    
    def selection_sort(self) -> None:
        """
        Selection Sort: Find minimum and place it at beginning.
        Time: O(n²) all cases
        Space: O(1)
        Stable: No
        """
        self.algorithm_name = "Selection Sort"
        n = len(self.arr)
        
        for i in range(n):
            min_idx = i
            self.states[min_idx] = State.MINIMUM
            
            # Find minimum in unsorted portion
            for j in range(i + 1, n):
                self._reset_states()
                self.states[min_idx] = State.MINIMUM
                self.states[j] = State.COMPARING
                self.display(f"{self.algorithm_name} - Finding minimum from index {i}")
                
                self.stats.comparisons += 1
                self.stats.array_accesses += 2
                if self.arr[j] < self.arr[min_idx]:
                    min_idx = j
                    self.states[min_idx] = State.MINIMUM
            
            # Swap minimum with current position
            if min_idx != i:
                self._swap(i, min_idx)
            
            self._mark_sorted(0, i)
        
        self._reset_states()
        self._mark_sorted(0, n - 1)
        self.display(f"{self.algorithm_name} - Complete!")
    
    def insertion_sort(self) -> None:
        """
        Insertion Sort: Build sorted array one element at a time.
        Time: O(n²) worst/avg, O(n) best
        Space: O(1)
        Stable: Yes
        """
        self.algorithm_name = "Insertion Sort"
        n = len(self.arr)
        
        for i in range(1, n):
            key = self.arr[i]
            j = i - 1
            
            # Shift elements greater than key
            while j >= 0:
                self._reset_states()
                self.states[j] = State.COMPARING
                self.states[i] = State.SWAPPING
                self._mark_sorted(0, i - 1)
                self.display(f"{self.algorithm_name} - Inserting {key} at correct position")
                
                self.stats.comparisons += 1
                self.stats.array_accesses += 1
                
                if self.arr[j] > key:
                    self.stats.array_accesses += 1
                    self.arr[j + 1] = self.arr[j]
                    j -= 1
                else:
                    break
            
            self.arr[j + 1] = key
            self.stats.array_accesses += 1
            self._mark_sorted(0, i)
        
        self._reset_states()
        self._mark_sorted(0, n - 1)
        self.display(f"{self.algorithm_name} - Complete!")
    
    def merge_sort(self) -> None:
        """
        Merge Sort: Divide and conquer with merging.
        Time: O(n log n) all cases
        Space: O(n)
        Stable: Yes
        """
        self.algorithm_name = "Merge Sort"
        
        def merge_sort_helper(left: int, right: int) -> None:
            if left >= right:
                return
            
            self.stats.recursive_calls += 1
            mid = (left + right) // 2
            
            # Visualize division
            self._reset_states()
            for i in range(left, mid + 1):
                self.states[i] = State.COMPARING
            for i in range(mid + 1, right + 1):
                self.states[i] = State.SWAPPING
            self.display(f"{self.algorithm_name} - Dividing [{left}:{mid}] and [{mid+1}:{right}]")
            
            # Recursive calls
            merge_sort_helper(left, mid)
            merge_sort_helper(mid + 1, right)
            
            # Merge
            merge(left, mid, right)
        
        def merge(left: int, mid: int, right: int) -> None:
            # Create temp arrays
            left_arr = self.arr[left:mid + 1]
            right_arr = self.arr[mid + 1:right + 1]
            
            i = j = 0
            k = left
            
            # Merge process
            while i < len(left_arr) and j < len(right_arr):
                self.stats.comparisons += 1
                self.stats.array_accesses += 2
                
                self._reset_states()
                self.states[k] = State.SWAPPING
                self.display(f"{self.algorithm_name} - Merging [{left}:{right}]")
                
                if left_arr[i] <= right_arr[j]:
                    self.arr[k] = left_arr[i]
                    i += 1
                else:
                    self.arr[k] = right_arr[j]
                    j += 1
                k += 1
                self.stats.array_accesses += 1
            
            # Copy remaining elements
            while i < len(left_arr):
                self.arr[k] = left_arr[i]
                i += 1
                k += 1
                self.stats.array_accesses += 1
            
            while j < len(right_arr):
                self.arr[k] = right_arr[j]
                j += 1
                k += 1
                self.stats.array_accesses += 1
        
        merge_sort_helper(0, len(self.arr) - 1)
        
        self._reset_states()
        self._mark_sorted(0, len(self.arr) - 1)
        self.display(f"{self.algorithm_name} - Complete!")
    
    def quick_sort(self) -> None:
        """
        Quick Sort: Divide using pivot partitioning.
        Time: O(n log n) avg, O(n²) worst
        Space: O(log n) for recursion
        Stable: No
        """
        self.algorithm_name = "Quick Sort"
        
        def quick_sort_helper(low: int, high: int) -> None:
            if low >= high:
                return
            
            self.stats.recursive_calls += 1
            
            # Partition
            pivot_idx = partition(low, high)
            
            # Recursive calls
            quick_sort_helper(low, pivot_idx - 1)
            quick_sort_helper(pivot_idx + 1, high)
        
        def partition(low: int, high: int) -> int:
            # Choose last element as pivot
            pivot = self.arr[high]
            
            self._reset_states()
            self.states[high] = State.PIVOT
            self.display(f"{self.algorithm_name} - Pivot: {pivot} at index {high}")
            
            i = low - 1
            
            for j in range(low, high):
                self._reset_states()
                self.states[high] = State.PIVOT
                self.states[j] = State.COMPARING
                self.display(f"{self.algorithm_name} - Partitioning around pivot {pivot}")
                
                self.stats.comparisons += 1
                self.stats.array_accesses += 1
                
                if self.arr[j] < pivot:
                    i += 1
                    if i != j:
                        self._swap(i, j)
                        self.states[high] = State.PIVOT
            
            # Place pivot in correct position
            self._swap(i + 1, high)
            self._mark_sorted(i + 1, i + 1)
            
            return i + 1
        
        quick_sort_helper(0, len(self.arr) - 1)
        
        self._reset_states()
        self._mark_sorted(0, len(self.arr) - 1)
        self.display(f"{self.algorithm_name} - Complete!")
    
    def heap_sort(self) -> None:
        """
        Heap Sort: Build max heap then extract elements.
        Time: O(n log n) all cases
        Space: O(1)
        Stable: No
        """
        self.algorithm_name = "Heap Sort"
        n = len(self.arr)
        
        def heapify(n: int, i: int) -> None:
            largest = i
            left = 2 * i + 1
            right = 2 * i + 2
            
            # Find largest among root, left, right
            if left < n:
                self.stats.comparisons += 1
                self.stats.array_accesses += 2
                self._reset_states()
                self.states[i] = State.PIVOT
                self.states[left] = State.COMPARING
                self.display(f"{self.algorithm_name} - Heapifying subtree at index {i}")
                
                if self.arr[left] > self.arr[largest]:
                    largest = left
            
            if right < n:
                self.stats.comparisons += 1
                self.stats.array_accesses += 2
                self._reset_states()
                self.states[i] = State.PIVOT
                self.states[right] = State.COMPARING
                self.display(f"{self.algorithm_name} - Heapifying subtree at index {i}")
                
                if self.arr[right] > self.arr[largest]:
                    largest = right
            
            # Swap and continue heapifying
            if largest != i:
                self._swap(i, largest)
                heapify(n, largest)
        
        # Build max heap
        for i in range(n // 2 - 1, -1, -1):
            heapify(n, i)
        
        # Extract elements from heap
        for i in range(n - 1, 0, -1):
            self._swap(0, i)
            self._mark_sorted(i, n - 1)
            heapify(i, 0)
        
        self._reset_states()
        self._mark_sorted(0, n - 1)
        self.display(f"{self.algorithm_name} - Complete!")
    
    def counting_sort(self) -> None:
        """
        Counting Sort: Count occurrences and reconstruct.
        Time: O(n + k) where k is range
        Space: O(k)
        Stable: Yes
        """
        self.algorithm_name = "Counting Sort"
        
        if not self.arr:
            return
        
        # Find range
        min_val = min(self.arr)
        max_val = max(self.arr)
        range_size = max_val - min_val + 1
        
        # Count occurrences
        count = [0] * range_size
        for num in self.arr:
            count[num - min_val] += 1
            self.stats.array_accesses += 1
        
        # Cumulative count
        for i in range(1, range_size):
            count[i] += count[i - 1]
        
        # Build output array
        output = [0] * len(self.arr)
        for i in range(len(self.arr) - 1, -1, -1):
            output[count[self.arr[i] - min_val] - 1] = self.arr[i]
            count[self.arr[i] - min_val] -= 1
            self.stats.array_accesses += 2
        
        # Copy back with visualization
        for i, val in enumerate(output):
            self.arr[i] = val
            self._reset_states()
            self._mark_sorted(0, i)
            self.display(f"{self.algorithm_name} - Placing elements in sorted order")
        
        self._reset_states()
        self._mark_sorted(0, len(self.arr) - 1)
        self.display(f"{self.algorithm_name} - Complete!")


# ==================== INTERACTIVE MODE ====================

def interactive_mode():
    """Interactive sorting exploration environment."""
    
    print("""
╔═══════════════════════════════════════════════════════════════╗
║         📊 ELITE ARRAY & SORTING VISUALIZER 📊                ║
║                                                               ║
║  Master sorting algorithms through visualization              ║
╚═══════════════════════════════════════════════════════════════╝

Commands:
  array <numbers>       - Set array (e.g., array 5 2 8 1 9)
  random <size>         - Generate random array
  sort <algorithm>      - Sort using algorithm
  speed <delay>         - Set animation speed (0.1 to 2.0)
  compare <alg1> <alg2> - Compare two algorithms
  reset                 - Reset to original array
  help                  - Show this help
  quit                  - Exit

Algorithms:
  bubble, selection, insertion, merge, quick, heap, counting

Examples:
  > array 64 34 25 12 22 11 90
  > sort bubble
  > speed 0.5
  > sort quick
""")
    
    current_array = [64, 34, 25, 12, 22, 11, 90]
    delay = 0.3
    
    while True:
        try:
            cmd = input("\n📊 > ").strip()
            
            if not cmd:
                continue
            
            parts = cmd.split()
            action = parts[0].lower()
            
            if action == "quit":
                print("Happy learning! 🚀")
                break
            
            elif action == "array":
                current_array = [int(x) for x in parts[1:]]
                print(f"Array set: {current_array}")
            
            elif action == "random":
                size = int(parts[1]) if len(parts) > 1 else 10
                import random
                current_array = [random.randint(1, 100) for _ in range(size)]
                print(f"Generated random array: {current_array}")
            
            elif action == "sort":
                if len(parts) < 2:
                    print("Usage: sort <algorithm>")
                    continue
                
                algorithm = parts[1].lower()
                viz = ArrayVisualizer(current_array, delay)
                
                algorithms = {
                    'bubble': viz.bubble_sort,
                    'selection': viz.selection_sort,
                    'insertion': viz.insertion_sort,
                    'merge': viz.merge_sort,
                    'quick': viz.quick_sort,
                    'heap': viz.heap_sort,
                    'counting': viz.counting_sort,
                }
                
                if algorithm in algorithms:
                    algorithms[algorithm]()
                    input("\nPress Enter to continue...")
                else:
                    print(f"Unknown algorithm: {algorithm}")
            
            elif action == "speed":
                delay = float(parts[1]) if len(parts) > 1 else 0.3
                delay = max(0.1, min(2.0, delay))
                print(f"Speed set to {delay}s per step")
            
            elif action == "compare":
                if len(parts) < 3:
                    print("Usage: compare <alg1> <alg2>")
                    continue
                
                alg1, alg2 = parts[1].lower(), parts[2].lower()
                
                # Run first algorithm
                viz1 = ArrayVisualizer(current_array, delay)
                algorithms = {
                    'bubble': viz1.bubble_sort,
                    'selection': viz1.selection_sort,
                    'insertion': viz1.insertion_sort,
                    'merge': viz1.merge_sort,
                    'quick': viz1.quick_sort,
                    'heap': viz1.heap_sort,
                    'counting': viz1.counting_sort,
                }
                
                if alg1 in algorithms:
                    algorithms[alg1]()
                    stats1 = viz1.stats
                    input("\nPress Enter for next algorithm...")
                else:
                    print(f"Unknown algorithm: {alg1}")
                    continue
                
                # Run second algorithm
                viz2 = ArrayVisualizer(current_array, delay)
                algorithms2 = {
                    'bubble': viz2.bubble_sort,
                    'selection': viz2.selection_sort,
                    'insertion': viz2.insertion_sort,
                    'merge': viz2.merge_sort,
                    'quick': viz2.quick_sort,
                    'heap': viz2.heap_sort,
                    'counting': viz2.counting_sort,
                }
                
                if alg2 in algorithms2:
                    algorithms2[alg2]()
                    stats2 = viz2.stats
                else:
                    print(f"Unknown algorithm: {alg2}")
                    continue
                
                # Comparison
                print("\n" + "="*80)
                print(f"COMPARISON: {alg1.upper()} vs {alg2.upper()}")
                print("="*80)
                print(f"{'Metric':<20} {alg1.upper():<20} {alg2.upper():<20}")
                print("-"*80)
                print(f"{'Comparisons':<20} {stats1.comparisons:<20} {stats2.comparisons:<20}")
                print(f"{'Swaps':<20} {stats1.swaps:<20} {stats2.swaps:<20}")
                print(f"{'Array Accesses':<20} {stats1.array_accesses:<20} {stats2.array_accesses:<20}")
                print("="*80)
                
                input("\nPress Enter to continue...")
            
            elif action == "reset":
                print(f"Array reset to: {current_array}")
            
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
    
    delay = 0.5
    
    print("\n" + "="*80)
    print("📚 DEMO 1: Bubble Sort (Simple but Slow)")
    print("="*80)
    arr1 = [64, 34, 25, 12, 22, 11, 90]
    viz1 = ArrayVisualizer(arr1, delay)
    viz1.bubble_sort()
    input("\nPress Enter for next demo...")
    
    print("\n" + "="*80)
    print("📚 DEMO 2: Quick Sort (Fast Average Case)")
    print("="*80)
    arr2 = [64, 34, 25, 12, 22, 11, 90]
    viz2 = ArrayVisualizer(arr2, delay)
    viz2.quick_sort()
    input("\nPress Enter for next demo...")
    
    print("\n" + "="*80)
    print("📚 DEMO 3: Merge Sort (Consistent Performance)")
    print("="*80)
    arr3 = [64, 34, 25, 12, 22, 11, 90]
    viz3 = ArrayVisualizer(arr3, delay)
    viz3.merge_sort()
    input("\nPress Enter for next demo...")


# ==================== MAIN ENTRY POINT ====================

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_examples()
    else:
        interactive_mode()