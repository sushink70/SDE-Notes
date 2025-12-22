from advanced_tracer import configure, trace

# Minimal output
configure(
    show_locals=False,
    show_timing=False,
    color=False
)

# Debug mode - maximum detail
configure(
    show_locals=True,
    show_timing=True,
    show_line_numbers=True,
    collapse_duplicates=False,  # Show all calls even duplicates
    max_depth=None,
    color=True
)

# Performance profiling
configure(
    show_locals=False,
    show_timing=True,
    collapse_duplicates=True,
    max_depth=10
)