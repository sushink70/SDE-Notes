import sys
import time
import inspect
import traceback
from functools import wraps
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import json

@dataclass
class CallFrame:
    call_id: int
    func_name: str
    args: Dict[str, Any]
    locals_on_entry: Dict[str, Any]
    locals_on_exit: Dict[str, Any] = field(default_factory=dict)
    return_value: Any = None
    exception: Optional[Exception] = None
    depth: int = 0
    parent_id: Optional[int] = None
    children: List[int] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0
    line_number: int = 0
    
    @property
    def duration_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000

class AdvancedRecursionTracer:
    def __init__(self, 
                 show_locals: bool = True,
                 show_timing: bool = True,
                 show_memory: bool = False,
                 max_depth: Optional[int] = None,
                 track_values: bool = True,
                 collapse_duplicates: bool = False,
                 show_line_numbers: bool = True,
                 color: bool = True):
        
        self.show_locals = show_locals
        self.show_timing = show_timing
        self.show_memory = show_memory
        self.max_depth = max_depth
        self.track_values = track_values
        self.collapse_duplicates = collapse_duplicates
        self.show_line_numbers = show_line_numbers
        self.color = color
        
        self.depth = 0
        self.call_count = 0
        self.frames: Dict[int, CallFrame] = {}
        self.call_stack: List[int] = []
        self.memo_cache: Dict[str, List[int]] = defaultdict(list)
        
        # Color codes
        self.COLORS = {
            'CYAN': '\033[96m',
            'GREEN': '\033[92m',
            'YELLOW': '\033[93m',
            'RED': '\033[91m',
            'BLUE': '\033[94m',
            'MAGENTA': '\033[95m',
            'GRAY': '\033[90m',
            'BOLD': '\033[1m',
            'END': '\033[0m'
        } if color else {k: '' for k in ['CYAN', 'GREEN', 'YELLOW', 'RED', 'BLUE', 'MAGENTA', 'GRAY', 'BOLD', 'END']}
        
    def _colorize(self, text: str, color: str) -> str:
        return f"{self.COLORS.get(color, '')}{text}{self.COLORS['END']}"
    
    def _format_value(self, value: Any, max_len: int = 50) -> str:
        try:
            repr_val = repr(value)
            if len(repr_val) > max_len:
                return repr_val[:max_len] + "..."
            return repr_val
        except:
            return f"<{type(value).__name__}>"
    
    def _get_cache_key(self, func_name: str, args: Dict[str, Any]) -> str:
        try:
            args_tuple = tuple(sorted((k, v) for k, v in args.items() if k != 'memo'))
            return f"{func_name}:{args_tuple}"
        except:
            return f"{func_name}:uncacheable"
    
    def _detect_memoization(self, func_name: str, args: Dict[str, Any], call_id: int) -> Optional[int]:
        cache_key = self._get_cache_key(func_name, args)
        previous_calls = self.memo_cache[cache_key]
        
        if previous_calls:
            return previous_calls[0]
        
        self.memo_cache[cache_key].append(call_id)
        return None
    
    def _print_indent(self, depth: int, is_last: bool = False, is_entry: bool = True) -> str:
        if depth == 0:
            return ""
        
        indent = ""
        for i in range(depth):
            if i < depth - 1:
                indent += "│   "
            else:
                if is_entry:
                    indent += "┌─ "
                else:
                    indent += "└─ "
        return indent
    
    def _print_frame_entry(self, frame: CallFrame):
        indent = self._print_indent(frame.depth, is_entry=True)
        
        # Call header
        args_str = ", ".join(f"{k}={self._colorize(self._format_value(v), 'YELLOW')}" 
                            for k, v in frame.args.items())
        
        header = f"{indent}{self._colorize(f'[{frame.call_id}]', 'CYAN')} {self._colorize(frame.func_name, 'BOLD')}({args_str})"
        
        if self.show_line_numbers and frame.line_number:
            header += self._colorize(f" @line {frame.line_number}", 'GRAY')
        
        print(header)
        
        # Check memoization
        if self.collapse_duplicates:
            memo_id = self._detect_memoization(frame.func_name, frame.args, frame.call_id)
            if memo_id:
                memo_indent = "│   " * frame.depth
                print(f"{memo_indent}{self._colorize(f'⚡ CACHED from call [{memo_id}]', 'MAGENTA')}")
        
        # Local variables on entry
        if self.show_locals and frame.locals_on_entry:
            for key, val in frame.locals_on_entry.items():
                if key not in frame.args:
                    var_indent = "│   " * (frame.depth + 1)
                    print(f"{var_indent}{self._colorize('●', 'BLUE')} {key} = {self._format_value(val)}")
    
    def _print_frame_exit(self, frame: CallFrame):
        indent = self._print_indent(frame.depth, is_last=True, is_entry=False)
        
        # Return value
        if frame.exception:
            result_str = self._colorize(f"✗ {type(frame.exception).__name__}: {frame.exception}", 'RED')
        else:
            result_str = self._colorize(f"→ {self._format_value(frame.return_value)}", 'GREEN')
        
        output = f"{indent}{self._colorize(f'[{frame.call_id}]', 'CYAN')} {result_str}"
        
        # Timing
        if self.show_timing:
            output += self._colorize(f" ({frame.duration_ms:.3f}ms)", 'GRAY')
        
        # Changed locals
        if self.show_locals and frame.locals_on_exit:
            changed = {k: v for k, v in frame.locals_on_exit.items() 
                      if k not in frame.args and k not in frame.locals_on_entry}
            if changed:
                output += self._colorize(f" [locals: {len(changed)} changed]", 'GRAY')
        
        print(output)
        
        # Show changed variables
        if self.show_locals and frame.locals_on_exit:
            for key, val in frame.locals_on_exit.items():
                if key not in frame.args and key not in frame.locals_on_entry:
                    var_indent = "│   " * frame.depth + "  "
                    print(f"{var_indent}{self._colorize('◆', 'MAGENTA')} {key} = {self._format_value(val)}")
    
    def trace(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.call_count += 1
            call_id = self.call_count
            
            # Depth check
            if self.max_depth and self.depth >= self.max_depth:
                print(self._colorize(f"⚠ Max depth {self.max_depth} reached, skipping deeper calls", 'YELLOW'))
                return func(*args, **kwargs)
            
            # Get function info
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Get source line
            try:
                line_number = inspect.getsourcelines(func)[1]
            except:
                line_number = 0
            
            # Create frame
            parent_id = self.call_stack[-1] if self.call_stack else None
            frame = CallFrame(
                call_id=call_id,
                func_name=func.__name__,
                args=dict(bound_args.arguments),
                locals_on_entry={},
                depth=self.depth,
                parent_id=parent_id,
                start_time=time.perf_counter(),
                line_number=line_number
            )
            
            self.frames[call_id] = frame
            self.call_stack.append(call_id)
            
            if parent_id:
                self.frames[parent_id].children.append(call_id)
            
            # Print entry
            self._print_frame_entry(frame)
            
            self.depth += 1
            try:
                result = func(*args, **kwargs)
                
                frame.return_value = result
                frame.end_time = time.perf_counter()
                
                self.depth -= 1
                self.call_stack.pop()
                
                # Print exit
                self._print_frame_exit(frame)
                
                return result
                
            except Exception as e:
                frame.exception = e
                frame.end_time = time.perf_counter()
                
                self.depth -= 1
                self.call_stack.pop()
                
                # Print exit
                self._print_frame_exit(frame)
                raise
        
        return wrapper
    
    def print_stats(self):
        """Print execution statistics"""
        print(f"\n{self._colorize('═' * 60, 'CYAN')}")
        print(f"{self._colorize('EXECUTION STATISTICS', 'BOLD')}")
        print(f"{self._colorize('═' * 60, 'CYAN')}\n")
        
        if not self.frames:
            print(self._colorize("No function calls recorded.", 'YELLOW'))
            return
        
        total_calls = len(self.frames)
        total_time = sum(f.duration_ms for f in self.frames.values())
        max_depth = max(f.depth for f in self.frames.values())
        
        print(f"Total calls: {self._colorize(str(total_calls), 'YELLOW')}")
        print(f"Total time: {self._colorize(f'{total_time:.3f}ms', 'YELLOW')}")
        print(f"Max depth: {self._colorize(str(max_depth), 'YELLOW')}")
        
        # Function breakdown
        func_stats = defaultdict(lambda: {'count': 0, 'time': 0.0})
        for frame in self.frames.values():
            func_stats[frame.func_name]['count'] += 1
            func_stats[frame.func_name]['time'] += frame.duration_ms
        
        print(f"\n{self._colorize('Per-function breakdown:', 'BOLD')}")
        for func_name, stats in sorted(func_stats.items()):
            print(f"  {func_name}: {stats['count']} calls, {stats['time']:.3f}ms total")
        
        # Slowest calls
        slowest = sorted(self.frames.values(), key=lambda f: f.duration_ms, reverse=True)[:5]
        if slowest:
            print(f"\n{self._colorize('Slowest calls:', 'BOLD')}")
            for frame in slowest:
                args_str = ", ".join(f"{k}={self._format_value(v, 20)}" for k, v in frame.args.items())
                print(f"  [{frame.call_id}] {frame.func_name}({args_str}): {frame.duration_ms:.3f}ms")
    
    def export_call_tree(self, filename: str = "call_tree.json"):
        """Export call tree to JSON"""
        if not self.frames:
            print(self._colorize("No function calls to export.", 'YELLOW'))
            return
        
        def frame_to_dict(frame: CallFrame) -> dict:
            return {
                'call_id': frame.call_id,
                'func_name': frame.func_name,
                'args': {k: str(v) for k, v in frame.args.items()},
                'return_value': str(frame.return_value),
                'duration_ms': frame.duration_ms,
                'depth': frame.depth,
                'children': [frame_to_dict(self.frames[cid]) for cid in frame.children]
            }
        
        roots = [f for f in self.frames.values() if f.parent_id is None]
        tree = [frame_to_dict(root) for root in roots]
        
        with open(filename, 'w') as f:
            json.dump(tree, f, indent=2)
        
        print(f"\n{self._colorize(f'Call tree exported to {filename}', 'GREEN')}")
    
    def reset(self):
        """Reset tracer state"""
        self.depth = 0
        self.call_count = 0
        self.frames.clear()
        self.call_stack.clear()
        self.memo_cache.clear()


# Global instance
tracer = AdvancedRecursionTracer(
    show_locals=True,
    show_timing=True,
    max_depth=None,
    collapse_duplicates=True,
    color=True
)

def trace(func):
    """Decorator for tracing"""
    return tracer.trace(func)

def configure(**kwargs):
    """Reconfigure tracer settings without replacing instance"""
    global tracer
    for key, value in kwargs.items():
        if hasattr(tracer, key):
            setattr(tracer, key, value)

def stats():
    """Print statistics"""
    tracer.print_stats()

def export(filename: str = "call_tree.json"):
    """Export call tree"""
    tracer.export_call_tree(filename)

def reset():
    """Reset tracer"""
    tracer.reset()