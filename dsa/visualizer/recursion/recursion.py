import functools
from typing import Any, Callable, List, Dict
from collections import defaultdict
import inspect

class RecursionVisualizer:
    """
    Advanced recursion tracer for understanding call stack behavior.
    
    Key Concepts Revealed:
    - Call stack growth/shrinkage (space complexity)
    - Parameter evolution through recursive calls
    - Base case detection and unwinding
    - Memoization impact on call count
    
    Complexity Analysis:
    - Time overhead: O(d) per call where d = depth
    - Space overhead: O(d * p) where p = parameters stored
    """
    
    def __init__(self):
        self.call_stack: List[Dict[str, Any]] = []
        self.call_count = 0
        self.max_depth = 0
        self.trace_log: List[str] = []
        self.memoization_hits = 0
        self.memoization_cache = {}
        
    def reset(self):
        """Clear all tracking state between runs."""
        self.call_stack.clear()
        self.call_count = 0
        self.max_depth = 0
        self.trace_log.clear()
        self.memoization_hits = 0
        self.memoization_cache.clear()
    
    def trace(self, func: Callable, use_memo: bool = False) -> Callable:
        """
        Decorator that instruments any recursive function.
        
        Args:
            func: Function to trace
            use_memo: Enable memoization to show optimization impact
        
        Returns:
            Wrapped function with full tracing capabilities
        """
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate unique call ID
            call_id = self.call_count
            self.call_count += 1
            current_depth = len(self.call_stack)
            self.max_depth = max(self.max_depth, current_depth)
            
            # Format arguments for display
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            args_str = ', '.join(f"{k}={v}" for k, v in bound_args.arguments.items())
            
            # Check memoization cache
            cache_key = (args, tuple(sorted(kwargs.items())))
            is_cached = use_memo and cache_key in self.memoization_cache
            
            if is_cached:
                self.memoization_hits += 1
                result = self.memoization_cache[cache_key]
                self._log_cached_call(func.__name__, args_str, result, current_depth)
                return result
            
            # Record entry
            call_info = {
                'id': call_id,
                'name': func.__name__,
                'args': args_str,
                'depth': current_depth,
                'status': 'entered'
            }
            self.call_stack.append(call_info)
            self._log_entry(call_info)
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Record exit
                call_info['status'] = 'returning'
                call_info['result'] = result
                self._log_exit(call_info)
                
                # Store in cache
                if use_memo:
                    self.memoization_cache[cache_key] = result
                
                self.call_stack.pop()
                return result
                
            except Exception as e:
                # Record exception
                call_info['status'] = 'exception'
                call_info['error'] = str(e)
                self._log_exception(call_info, e)
                self.call_stack.pop()
                raise
        
        return wrapper
    
    def _log_entry(self, call_info: Dict[str, Any]):
        """Log function entry with visual call stack."""
        indent = "│   " * call_info['depth']
        arrow = "┌─► " if call_info['depth'] > 0 else "► "
        
        log_line = (
            f"{indent}{arrow}CALL #{call_info['id']}: "
            f"{call_info['name']}({call_info['args']})"
        )
        self.trace_log.append(log_line)
        
        # Show current stack state
        if call_info['depth'] > 0:
            stack_visual = self._render_stack_state()
            self.trace_log.append(f"{indent}│   Stack depth: {len(self.call_stack)}")
    
    def _log_exit(self, call_info: Dict[str, Any]):
        """Log function return with result."""
        indent = "│   " * call_info['depth']
        arrow = "└─◄ " if call_info['depth'] > 0 else "◄ "
        
        log_line = (
            f"{indent}{arrow}RETURN #{call_info['id']}: "
            f"{call_info['name']} = {call_info['result']}"
        )
        self.trace_log.append(log_line)
    
    def _log_cached_call(self, func_name: str, args_str: str, result: Any, depth: int):
        """Log memoization cache hit."""
        indent = "│   " * depth
        log_line = (
            f"{indent}⚡ CACHED: {func_name}({args_str}) = {result}"
        )
        self.trace_log.append(log_line)
    
    def _log_exception(self, call_info: Dict[str, Any], error: Exception):
        """Log exception during execution."""
        indent = "│   " * call_info['depth']
        log_line = (
            f"{indent}✗ EXCEPTION #{call_info['id']}: "
            f"{type(error).__name__}: {str(error)}"
        )
        self.trace_log.append(log_line)
    
    def _render_stack_state(self) -> str:
        """Generate ASCII visualization of current call stack."""
        if not self.call_stack:
            return "Stack: [empty]"
        
        frames = []
        for frame in self.call_stack:
            frames.append(f"{frame['name']}({frame['args']})")
        
        return "Stack: [" + " → ".join(frames) + "]"
    
    def print_trace(self):
        """Display complete execution trace."""
        print("\n" + "═" * 80)
        print("RECURSION EXECUTION TRACE")
        print("═" * 80 + "\n")
        
        for line in self.trace_log:
            print(line)
        
        print("\n" + "═" * 80)
        print("EXECUTION STATISTICS")
        print("═" * 80)
        print(f"Total function calls: {self.call_count}")
        print(f"Maximum stack depth: {self.max_depth}")
        
        if self.memoization_cache:
            print(f"Memoization hits: {self.memoization_hits}")
            print(f"Cache size: {len(self.memoization_cache)}")
            cache_hit_rate = (self.memoization_hits / self.call_count) * 100
            print(f"Cache hit rate: {cache_hit_rate:.1f}%")
        
        print("═" * 80 + "\n")
    
    def analyze_complexity(self):
        """Provide complexity analysis based on execution."""
        print("\n" + "═" * 80)
        print("COMPLEXITY ANALYSIS")
        print("═" * 80)
        
        print(f"\nTime Complexity Indicators:")
        print(f"  • Total calls: {self.call_count}")
        print(f"  • With memoization: O(n) possible if cache effective")
        print(f"  • Without memoization: Exponential growth possible")
        
        print(f"\nSpace Complexity Indicators:")
        print(f"  • Max recursion depth: {self.max_depth}")
        print(f"  • Call stack space: O({self.max_depth})")
        
        if self.memoization_cache:
            print(f"  • Memoization space: O({len(self.memoization_cache)})")
        
        print("═" * 80 + "\n")


# ═══════════════════════════════════════════════════════════
# EXAMPLE PROBLEMS - CLASSIC RECURSION PATTERNS
# ═══════════════════════════════════════════════════════════

def demo_fibonacci():
    """
    Fibonacci: Classic exponential recursion without memoization.
    Pattern: Two recursive calls per invocation.
    """
    print("\n" + "█" * 80)
    print("DEMO 1: FIBONACCI (Exponential Recursion)")
    print("█" * 80)
    
    visualizer = RecursionVisualizer()
    
    @visualizer.trace
    def fib(n):
        if n <= 1:
            return n
        return fib(n - 1) + fib(n - 2)
    
    print("\n--- WITHOUT MEMOIZATION ---")
    visualizer.reset()
    result = fib(5)
    print(f"\nResult: fib(5) = {result}")
    visualizer.print_trace()
    visualizer.analyze_complexity()
    
    # Now with memoization
    print("\n--- WITH MEMOIZATION ---")
    visualizer.reset()
    
    @visualizer.trace(use_memo=True)
    def fib_memo(n):
        if n <= 1:
            return n
        return fib_memo(n - 1) + fib_memo(n - 2)
    
    result = fib_memo(5)
    print(f"\nResult: fib_memo(5) = {result}")
    visualizer.print_trace()
    visualizer.analyze_complexity()


def demo_factorial():
    """
    Factorial: Linear recursion with tail call potential.
    Pattern: Single recursive call per invocation.
    """
    print("\n" + "█" * 80)
    print("DEMO 2: FACTORIAL (Linear Recursion)")
    print("█" * 80)
    
    visualizer = RecursionVisualizer()
    
    @visualizer.trace
    def factorial(n):
        if n <= 1:
            return 1
        return n * factorial(n - 1)
    
    result = factorial(5)
    print(f"\nResult: 5! = {result}")
    visualizer.print_trace()
    visualizer.analyze_complexity()


def demo_binary_search():
    """
    Binary Search: Logarithmic recursion depth.
    Pattern: Single recursive call with halved input.
    """
    print("\n" + "█" * 80)
    print("DEMO 3: BINARY SEARCH (Logarithmic Recursion)")
    print("█" * 80)
    
    visualizer = RecursionVisualizer()
    
    @visualizer.trace
    def binary_search(arr, target, left, right):
        if left > right:
            return -1
        
        mid = (left + right) // 2
        
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            return binary_search(arr, target, mid + 1, right)
        else:
            return binary_search(arr, target, left, mid - 1)
    
    arr = [1, 3, 5, 7, 9, 11, 13, 15]
    target = 7
    result = binary_search(arr, target, 0, len(arr) - 1)
    print(f"\nSearching for {target} in {arr}")
    print(f"Result: Index = {result}")
    visualizer.print_trace()
    visualizer.analyze_complexity()


def demo_permutations():
    """
    Permutations: Branching recursion (backtracking).
    Pattern: Multiple recursive calls with state modification.
    """
    print("\n" + "█" * 80)
    print("DEMO 4: PERMUTATIONS (Backtracking Recursion)")
    print("█" * 80)
    
    visualizer = RecursionVisualizer()
    
    @visualizer.trace
    def permute(nums, path, result):
        if len(path) == len(nums):
            result.append(path[:])
            return
        
        for num in nums:
            if num in path:
                continue
            path.append(num)
            permute(nums, path, result)
            path.pop()  # Backtrack
    
    nums = [1, 2, 3]
    result = []
    permute(nums, [], result)
    print(f"\nPermutations of {nums}:")
    for perm in result:
        print(f"  {perm}")
    visualizer.print_trace()
    visualizer.analyze_complexity()


def demo_tower_of_hanoi():
    """
    Tower of Hanoi: Classic recursive problem.
    Pattern: Two recursive calls with different parameters.
    """
    print("\n" + "█" * 80)
    print("DEMO 5: TOWER OF HANOI (Divide & Conquer)")
    print("█" * 80)
    
    visualizer = RecursionVisualizer()
    moves = []
    
    @visualizer.trace
    def hanoi(n, source, target, auxiliary):
        if n == 1:
            move = f"Move disk 1 from {source} to {target}"
            moves.append(move)
            return
        
        hanoi(n - 1, source, auxiliary, target)
        move = f"Move disk {n} from {source} to {target}"
        moves.append(move)
        hanoi(n - 1, auxiliary, target, source)
    
    hanoi(3, 'A', 'C', 'B')
    print("\nMoves required:")
    for i, move in enumerate(moves, 1):
        print(f"  {i}. {move}")
    visualizer.print_trace()
    visualizer.analyze_complexity()


# ═══════════════════════════════════════════════════════════
# INTERACTIVE MODE
# ═══════════════════════════════════════════════════════════

def interactive_mode():
    """Allow users to trace their own recursive functions."""
    print("\n" + "█" * 80)
    print("INTERACTIVE MODE - Trace Your Own Recursion")
    print("█" * 80)
    print("\nDefine your recursive function and see it visualized!")
    print("Example:")
    print("  def sum_n(n):")
    print("      if n == 0: return 0")
    print("      return n + sum_n(n - 1)")
    print("\nType 'done' when finished, then enter function call.")
    print("Type 'quit' to exit.\n")
    
    visualizer = RecursionVisualizer()
    
    while True:
        print("─" * 80)
        print("Enter your function definition (multi-line, 'done' to finish):")
        lines = []
        while True:
            line = input()
            if line.strip().lower() == 'done':
                break
            lines.append(line)
        
        if not lines:
            continue
        
        code = '\n'.join(lines)
        
        try:
            # Create namespace and execute definition
            namespace = {'visualizer': visualizer}
            exec(code, namespace)
            
            # Find the defined function
            func_name = None
            for name, obj in namespace.items():
                if callable(obj) and name != 'visualizer':
                    func_name = name
                    break
            
            if not func_name:
                print("❌ No function found in definition")
                continue
            
            # Wrap with tracer
            original_func = namespace[func_name]
            traced_func = visualizer.trace(original_func)
            namespace[func_name] = traced_func
            
            print(f"\n✓ Function '{func_name}' loaded and instrumented")
            print("Enter function call (e.g., sum_n(5)) or 'quit':")
            
            call = input().strip()
            if call.lower() == 'quit':
                break
            
            visualizer.reset()
            result = eval(call, namespace)
            print(f"\nResult: {result}")
            visualizer.print_trace()
            visualizer.analyze_complexity()
            
        except Exception as e:
            print(f"❌ Error: {e}")


# ═══════════════════════════════════════════════════════════
# MAIN DEMO RUNNER
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "RECURSION VISUALIZER DEMO SUITE" + " " * 27 + "║")
    print("╚" + "═" * 78 + "╝")
    
    demos = [
        ("Fibonacci", demo_fibonacci),
        ("Factorial", demo_factorial),
        ("Binary Search", demo_binary_search),
        ("Permutations", demo_permutations),
        ("Tower of Hanoi", demo_tower_of_hanoi),
    ]
    
    print("\nAvailable demos:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")
    print(f"  {len(demos) + 1}. Interactive Mode")
    print(f"  {len(demos) + 2}. Run All Demos")
    print("  0. Exit")
    
    while True:
        try:
            choice = input("\nSelect demo (0-{}): ".format(len(demos) + 2)).strip()
            
            if choice == '0':
                print("\n✓ Exiting. Keep practicing recursion!")
                break
            
            choice_num = int(choice)
            
            if choice_num == len(demos) + 1:
                interactive_mode()
            elif choice_num == len(demos) + 2:
                for name, demo_func in demos:
                    demo_func()
                    input("\nPress Enter to continue to next demo...")
            elif 1 <= choice_num <= len(demos):
                demos[choice_num - 1][1]()
            else:
                print("❌ Invalid choice")
                
        except ValueError:
            print("❌ Please enter a number")
        except KeyboardInterrupt:
            print("\n\n✓ Interrupted. Exiting.")
            break
        except Exception as e:
            print(f"❌ Error: {e}")