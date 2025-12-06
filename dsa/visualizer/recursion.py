import sys
import inspect
from functools import wraps
import traceback

class RecursionTracer:
    """
    A flexible recursion tracer for debugging and learning recursive functions.
    
    This class provides two main ways to trace recursion:
    1. **Decorator-based tracing**: Apply `@trace_recursion` to any function for automatic tracing.
       - Prints: Entry (with args/kwargs), local state (key locals), and exit (with return value).
       - Handles depth with indentation for call stack visualization.
    
    2. **Global tracing**: Use `start_tracing()` and `stop_tracing()` to trace all calls in a session.
       - Uses `sys.settrace` for fine-grained event tracing (call, line, return, exception).
       - Ideal for complex, multi-function recursion or when you can't decorate easily.
       - Filters to focus on recursive calls (e.g., same function name).
    
    Key Features:
    - **State Inspection**: On entry, dumps key local variables (configurable).
    - **Stack Visualization**: Indentation shows call depth; optional stack dump on error.
    - **Exception Handling**: Catches and traces errors with full stack.
    - **Customization**: Filter functions, depth limits, verbose levels.
    
    Usage Notes:
    - For learning: Start with decorator on simple funcs like factorial or Fibonacci.
    - For debugging: Use global trace in a REPL or script; watch for stack overflows.
    - Security/Performance: In production, disable tracing (O(n) overhead per call).
    - Aligns with systems engineering: Low-overhead, non-intrusive, extensible (e.g., integrate with eBPF for kernel recursion tracing).
    
    Example:
        @trace_recursion(verbose=True)
        def factorial(n):
            if n <= 1:
                return 1
            return n * factorial(n - 1)
        
        print(factorial(5))  # Traces the recursion tree
    """
    
    def __init__(self, max_depth=1000, verbose=False, filter_funcs=None):
        """
        Initialize the tracer.
        
        Args:
            max_depth (int): Raise error if recursion exceeds this (prevents stack overflow).
            verbose (bool): If True, dump full locals and line-by-line execution.
            filter_funcs (list[str] or None): List of function names to trace (default: all).
        """
        self.max_depth = max_depth
        self.verbose = verbose
        self.filter_funcs = filter_funcs or []
        self._call_stack = []  # Track depth and frames
        self._trace_func = None  # For global tracing
    
    def _get_indent(self):
        """Return indentation string based on current stack depth."""
        return '  ' * len(self._call_stack)
    
    def _dump_locals(self, frame):
        """Dump key local variables (non-recursive args + interesting vars)."""
        locals_dict = frame.f_locals
        # Filter to avoid dumping huge data structures or self/recursive refs
        safe_locals = {k: v for k, v in locals_dict.items()
                       if not k.startswith('__') and not callable(v) and
                       (isinstance(v, (int, float, str, bool)) or len(str(v)) < 100)}
        return safe_locals
    
    # Decorator Method (Fixed: Compute arg_str in wrapper using func signature)
    def trace_recursion(self, func):
        """Decorator: Wrap a function to trace its recursive calls."""
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_frame = inspect.currentframe()
            frame = current_frame.f_back if current_frame else None
            if self.filter_funcs and func.__name__ not in self.filter_funcs:
                return func(*args, **kwargs)  # Skip tracing
            
            # Compute arg_str using func's signature (fixes TypeError)
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            arg_str = ', '.join(f"{k}={v!r}" for k, v in bound_args.arguments.items())
            
            # Entry trace
            print(f"{self._get_indent()}+ CALL: {func.__name__}({arg_str})")
            if self.verbose:
                print(f"{self._get_indent()}  Locals on entry: {self._dump_locals(frame)}")
            
            self._call_stack.append(frame)
            if len(self._call_stack) > self.max_depth:
                raise RuntimeError(f"Recursion depth exceeded {self.max_depth} in {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                # Return trace
                print(f"{self._get_indent()}- RETURN: {func.__name__} -> {result!r}")
                self._call_stack.pop()
                return result
            except Exception as e:
                # Exception trace
                print(f"{self._get_indent()}! EXCEPTION in {func.__name__}: {e}")
                if self.verbose:
                    print(f"{self._get_indent()}  Full stack:\n{''.join(traceback.format_stack(frame))}")
                self._call_stack.pop()
                raise
        return wrapper
    
    # Global Tracing Methods (Simplified arg_str for 'call' event to avoid signature issues)
    def _global_trace(self, frame, event, arg):
        """Internal trace function for sys.settrace."""
        if event == 'call':
            code = frame.f_code
            func_name = code.co_name
            if self.filter_funcs and func_name not in self.filter_funcs:
                return self._global_trace  # Continue tracing but skip print
            
            # Check if recursive: simplistic, same func in stack
            is_recursive = any(f.f_code.co_name == func_name for f in self._call_stack)
            if is_recursive or self.filter_funcs:  # Trace only if filtered or recursive
                # Simplified arg_str: use varnames and f_locals (at 'call', locals may be partial)
                argcount = code.co_argcount
                varnames = code.co_varnames[:argcount]
                f_locals = frame.f_locals
                arg_items = [f"{varnames[i]}={f_locals.get(varnames[i], '<unbound>')!r}" 
                             for i in range(min(argcount, len(varnames)))]
                arg_str = ', '.join(arg_items)
                print(f"{self._get_indent()}+ CALL: {func_name}({arg_str})")
                if self.verbose:
                    print(f"{self._get_indent()}  Locals on entry: {self._dump_locals(frame)}")
                self._call_stack.append(frame)
        
        elif event == 'return':
            if self._call_stack and self._call_stack[-1] is frame:
                func_name = frame.f_code.co_name
                print(f"{self._get_indent()}- RETURN: {func_name} -> {arg!r}")
                self._call_stack.pop()
        
        elif event == 'exception':
            if self._call_stack and self._call_stack[-1] is frame:
                func_name = frame.f_code.co_name
                print(f"{self._get_indent()}! EXCEPTION in {func_name}: {arg[1]}")
                if self.verbose:
                    print(f"{self._get_indent()}  Full stack:\n{''.join(traceback.format_stack(frame))}")
                self._call_stack.pop()
        
        elif self.verbose and event == 'line':
            print(f"{self._get_indent()}  LINE: {frame.f_lineno} in {frame.f_code.co_name}")
        
        return self._global_trace
    
    def start_tracing(self):
        """Start global tracing for the current thread/session."""
        if self._trace_func:
            print("Tracing already active.")
            return
        self._trace_func = self._global_trace
        sys.settrace(self._global_trace)
        print("Global recursion tracing started. Use stop_tracing() to halt.")
    
    def stop_tracing(self):
        """Stop global tracing."""
        sys.settrace(None)
        self._call_stack.clear()
        self._trace_func = None
        print("Global recursion tracing stopped.")
    
    def __enter__(self):
        """Context manager: Auto-start/stop tracing."""
        self.start_tracing()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_tracing()
        return False  # Re-raise exceptions

# Demonstration & Testing
def demo():
    """Interactive demo to showcase tracing on classic recursive problems."""
    tracer = RecursionTracer(max_depth=10, verbose=False)  # Set verbose=True for more details
    
    # Example 1: Factorial (simple tail recursion)
    @tracer.trace_recursion
    def factorial(n):
        if n <= 1:
            return 1
        return n * factorial(n - 1)
    
    print("=== Factorial(5) with Decorator Tracing ===")
    print(f"Result: {factorial(5)}\n")
    
    # Example 2: Fibonacci (inefficient, shows branching recursion)
    @tracer.trace_recursion
    def fib(n):
        if n <= 1:
            return n
        return fib(n-1) + fib(n-2)
    
    print("=== Fibonacci(4) with Decorator Tracing ===")
    print(f"Result: {fib(4)}\n")
    
    # Example 3: Tree Traversal (from your previous TreeVisualizer)
    class TreeNode:
        def __init__(self, val, left=None, right=None):
            self.val = val
            self.left = left
            self.right = right
    
    # Simple inorder traversal
    def inorder_traversal(root):
        if not root:
            return []
        return inorder_traversal(root.left) + [root.val] + inorder_traversal(root.right)
    
    # Build a small tree
    root = TreeNode(1, TreeNode(2), TreeNode(3, TreeNode(4)))
    
    print("=== Inorder Traversal with Decorator Tracing ===")
    @tracer.trace_recursion
    def traced_inorder(root):
        if not root:
            return []
        return traced_inorder(root.left) + [root.val] + traced_inorder(root.right)
    
    print(f"Result: {traced_inorder(root)}\n")
    
    # Example 4: Global Tracing in Context
    print("=== Global Tracing: Factorial(3) ===")
    with tracer:
        def global_fact(n):
            if n <= 1:
                return 1
            return n * global_fact(n - 1)
        print(f"Result: {global_fact(3)}\n")
    
    # Interactive Mode: Trace your own function
    print("\n=== Interactive Debugger ===")
    print("Define a recursive function, decorate it with @tracer.trace_recursion,")
    print("or use 'with tracer:' for global trace. Call it to see tracing!")
    print("Example: tracer.trace_recursion(your_func)(*args)")
    print("Type 'quit' to exit demo.\n")
    
    while True:
        try:
            user_input = input("Enter a recursive call (e.g., 'factorial(6)') or 'quit': ").strip()
            if user_input.lower() == 'quit':
                break
            # Simple eval for demo (use cautiously in real code)
            if user_input in ['factorial(5)', 'fib(4)', 'traced_inorder(root)']:
                exec(user_input)
            else:
                print("Use one of the demo functions or define your own!")
        except Exception as e:
            print(f"Error: {e}")

# For deeper debugging: Integrate with pdb
def debug_with_pdb(func):
    """Decorator to drop into pdb on entry/exit (for step-by-step inspection)."""
    import pdb
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        pdb.set_trace()  # Break on entry
        result = func(*args, **kwargs)
        pdb.set_trace()  # Break on exit
        return result
    return wrapper

# Advanced: Custom Filter for Specific Recursion Patterns
def trace_only_recursion(tracer, func):
    """Trace only when the call is recursive (same func in stack)."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        current_frame = inspect.currentframe()
        frame = current_frame.f_back if current_frame else None
        if not frame:
            return func(*args, **kwargs)
        stack_funcs = [f.frame.f_code.co_name for f in inspect.getouterframes(frame)]
        if func.__name__ in stack_funcs[1:]:  # Already in stack
            # Simplified trace for recursive calls only
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            arg_str = ', '.join(f"{k}={v!r}" for k, v in bound_args.arguments.items())
            print(f"{tracer._get_indent()}+ RECURSIVE CALL: {func.__name__}({arg_str})")
        try:
            return func(*args, **kwargs)
        finally:
            if func.__name__ in stack_funcs[1:]:
                # Note: Return value hard to capture here; use global trace for full
                pass
    return wrapper

if __name__ == "__main__":
    demo()