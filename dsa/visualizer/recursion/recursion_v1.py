import functools
from typing import Any, Callable, List, Dict, Optional
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
    
    def trace(self, func: Optional[Callable] = None, *, use_memo: bool = False) -> Callable:
        """
        Decorator that instruments any recursive function.
        
        CRITICAL FIX: Now supports both usage patterns:
        1. @visualizer.trace (no arguments)
        2. @visualizer.trace(use_memo=True) (with arguments)
        
        Pattern: Decorator Factory
        - If called with arguments, returns a decorator
        - If called without arguments (just func), applies directly
        
        Args:
            func: Function to trace (None if called with arguments)
            use_memo: Enable memoization to show optimization impact
        
        Returns:
            Wrapped function with full tracing capabilities
        """
        
        def decorator(fn: Callable) -> Callable:
            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                # Generate unique call ID
                call_id = self.call_count
                self.call_count += 1
                current_depth = len(self.call_stack)
                self.max_depth = max(self.max_depth, current_depth + 1)  # FIX: +1 for current call
                
                # Format arguments for display
                try:
                    sig = inspect.signature(fn)
                    bound_args = sig.bind(*args, **kwargs)
                    bound_args.apply_defaults()
                    args_str = ', '.join(f"{k}={v}" for k, v in bound_args.arguments.items())
                except Exception:
                    # Fallback if signature binding fails
                    args_str = ', '.join(repr(arg) for arg in args)
                    if kwargs:
                        args_str += ', ' + ', '.join(f"{k}={v}" for k, v in kwargs.items())
                
                # Check memoization cache
                cache_key = (args, tuple(sorted(kwargs.items())))
                is_cached = use_memo and cache_key in self.memoization_cache
                
                if is_cached:
                    self.memoization_hits += 1
                    result = self.memoization_cache[cache_key]
                    self._log_cached_call(fn.__name__, args_str, result, current_depth)
                    return result
                
                # Record entry
                call_info = {
                    'id': call_id,
                    'name': fn.__name__,
                    'args': args_str,
                    'depth': current_depth,
                    'status': 'entered'
                }
                self.call_stack.append(call_info)
                self._log_entry(call_info)
                
                try:
                    # Execute function
                    result = fn(*args, **kwargs)
                    
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
                    if self.call_stack:  # FIX: Check before popping
                        self.call_stack.pop()
                    raise
            
            return wrapper
        
        # FIX: Decorator factory pattern
        if func is None:
            # Called with arguments: @visualizer.trace(use_memo=True)
            return decorator
        else:
            # Called without arguments: @visualizer.trace
            return decorator(func)
    
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
            if self.call_count > 0:
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
# COMPREHENSIVE TEST SUITE
# ═══════════════════════════════════════════════════════════

def run_all_tests():
    """Run comprehensive test suite to verify all functionality."""
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 25 + "RUNNING TEST SUITE" + " " * 35 + "║")
    print("╚" + "═" * 78 + "╝\n")
    
    tests = [
        test_fibonacci,
        test_fibonacci_memoization,
        test_factorial,
        test_binary_search,
        test_permutations,
        test_tower_of_hanoi,
        test_edge_cases,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
            print(f"✓ {test.__name__} PASSED\n")
        except AssertionError as e:
            failed += 1
            print(f"✗ {test.__name__} FAILED: {e}\n")
        except Exception as e:
            failed += 1
            print(f"✗ {test.__name__} ERROR: {e}\n")
    
    print("═" * 80)
    print(f"TEST SUMMARY: {passed} passed, {failed} failed")
    print("═" * 80 + "\n")


def test_fibonacci():
    """Test Fibonacci without memoization."""
    print("─" * 80)
    print("TEST: Fibonacci (Exponential Recursion)")
    print("─" * 80)
    
    visualizer = RecursionVisualizer()
    
    @visualizer.trace
    def fib(n):
        if n <= 1:
            return n
        return fib(n - 1) + fib(n - 2)
    
    result = fib(5)
    
    # Verify result
    assert result == 5, f"Expected 5, got {result}"
    
    # Verify call count (Fibonacci(5) makes 15 calls)
    assert visualizer.call_count == 15, f"Expected 15 calls, got {visualizer.call_count}"
    
    # Verify max depth
    assert visualizer.max_depth == 5, f"Expected depth 5, got {visualizer.max_depth}"
    
    print(f"Result: {result}")
    print(f"Calls: {visualizer.call_count}, Max Depth: {visualizer.max_depth}")


def test_fibonacci_memoization():
    """Test Fibonacci WITH memoization - CRITICAL BUG FIX TEST."""
    print("─" * 80)
    print("TEST: Fibonacci with Memoization (Bug Fix Verification)")
    print("─" * 80)
    
    visualizer = RecursionVisualizer()
    
    # THIS SHOULD NOW WORK - was the main bug
    @visualizer.trace(use_memo=True)
    def fib_memo(n):
        if n <= 1:
            return n
        return fib_memo(n - 1) + fib_memo(n - 2)
    
    result = fib_memo(5)
    
    # Verify result
    assert result == 5, f"Expected 5, got {result}"
    
    # With memoization, should make 11 calls (much less than 15)
    # fib(5) -> fib(4) -> fib(3) -> fib(2) -> fib(1), fib(0)
    # Then cached calls for repeated values
    print(f"Result: {result}")
    print(f"Calls: {visualizer.call_count} (vs 15 without memo)")
    print(f"Cache hits: {visualizer.memoization_hits}")
    print(f"Cache size: {len(visualizer.memoization_cache)}")
    
    # Should have cache hits
    assert visualizer.memoization_hits > 0, "Expected cache hits with memoization"


def test_factorial():
    """Test factorial (linear recursion)."""
    print("─" * 80)
    print("TEST: Factorial (Linear Recursion)")
    print("─" * 80)
    
    visualizer = RecursionVisualizer()
    
    @visualizer.trace
    def factorial(n):
        if n <= 1:
            return 1
        return n * factorial(n - 1)
    
    result = factorial(5)
    
    assert result == 120, f"Expected 120, got {result}"
    assert visualizer.call_count == 5, f"Expected 5 calls, got {visualizer.call_count}"
    assert visualizer.max_depth == 5, f"Expected depth 5, got {visualizer.max_depth}"
    
    print(f"Result: {result}")
    print(f"Calls: {visualizer.call_count}, Max Depth: {visualizer.max_depth}")


def test_binary_search():
    """Test binary search (logarithmic recursion)."""
    print("─" * 80)
    print("TEST: Binary Search (Logarithmic Recursion)")
    print("─" * 80)
    
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
    
    # Test finding element
    result = binary_search(arr, 7, 0, len(arr) - 1)
    assert result == 3, f"Expected index 3, got {result}"
    print(f"Found 7 at index: {result}, Calls: {visualizer.call_count}")
    
    # Test not finding element
    visualizer.reset()
    result = binary_search(arr, 10, 0, len(arr) - 1)
    assert result == -1, f"Expected -1, got {result}"
    print(f"Element 10 not found, Calls: {visualizer.call_count}")


def test_permutations():
    """Test permutations (backtracking)."""
    print("─" * 80)
    print("TEST: Permutations (Backtracking)")
    print("─" * 80)
    
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
            path.pop()
    
    nums = [1, 2, 3]
    result = []
    permute(nums, [], result)
    
    # Should generate 3! = 6 permutations
    assert len(result) == 6, f"Expected 6 permutations, got {len(result)}"
    
    # Verify all permutations are unique
    assert len(set(tuple(p) for p in result)) == 6, "Permutations not unique"
    
    print(f"Generated {len(result)} permutations")
    print(f"Calls: {visualizer.call_count}, Max Depth: {visualizer.max_depth}")


def test_tower_of_hanoi():
    """Test Tower of Hanoi."""
    print("─" * 80)
    print("TEST: Tower of Hanoi")
    print("─" * 80)
    
    visualizer = RecursionVisualizer()
    moves = []
    
    @visualizer.trace
    def hanoi(n, source, target, auxiliary):
        if n == 1:
            moves.append(f"Move disk 1 from {source} to {target}")
            return
        
        hanoi(n - 1, source, auxiliary, target)
        moves.append(f"Move disk {n} from {source} to {target}")
        hanoi(n - 1, auxiliary, target, source)
    
    hanoi(3, 'A', 'C', 'B')
    
    # Tower of Hanoi with n disks requires 2^n - 1 moves
    assert len(moves) == 7, f"Expected 7 moves, got {len(moves)}"
    
    # Calls: 2^n - 1 = 7
    assert visualizer.call_count == 7, f"Expected 7 calls, got {visualizer.call_count}"
    
    print(f"Moves: {len(moves)}, Calls: {visualizer.call_count}")


def test_edge_cases():
    """Test edge cases and error handling."""
    print("─" * 80)
    print("TEST: Edge Cases")
    print("─" * 80)
    
    visualizer = RecursionVisualizer()
    
    # Test with base case immediately
    @visualizer.trace
    def immediate_base(n):
        if n == 0:
            return 1
        return n * immediate_base(n - 1)
    
    result = immediate_base(0)
    assert result == 1, f"Expected 1, got {result}"
    assert visualizer.call_count == 1, f"Expected 1 call, got {visualizer.call_count}"
    print(f"✓ Immediate base case test passed")
    
    # Test exception handling
    visualizer.reset()
    
    @visualizer.trace
    def will_error(n):
        if n == 0:
            raise ValueError("Intentional error")
        return will_error(n - 1)
    
    try:
        will_error(2)
        assert False, "Should have raised ValueError"
    except ValueError:
        print(f"✓ Exception handling test passed")
        # Verify exception was logged
        assert any('EXCEPTION' in line for line in visualizer.trace_log), "Exception not logged"


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
    
    # Now with memoization - FIX APPLIED
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
            if line.strip().lower() == 'quit':
                return
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
            import traceback
            traceback.print_exc()


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
    
    print("\nAvailable options:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")
    print(f"  {len(demos) + 1}. Interactive Mode")
    print(f"  {len(demos) + 2}. Run All Demos")
    print(f"  {len(demos) + 3}. Run Test Suite")
    print("  0. Exit")
    
    while True:
        try:
            choice = input(f"\nSelect option (0-{len(demos) + 3}): ").strip()
            
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
            elif choice_num == len(demos) + 3:
                run_all_tests()
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
            import traceback
            traceback.print_exc()
