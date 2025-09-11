def manual_memoize(func):
    """Manual memoization decorator using a dictionary cache."""
    cache = {}
    
    
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__} with args: {args}")
        if args in cache:
            return cache[args]
        result = func(*args, **kwargs)
        cache[args] = result
        return result
    
    wrapper.cache = cache
    wrapper.cache_clear = lambda: cache.clear()
    return wrapper

# Example usage
@manual_memoize
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# Test the function
print(f"fibonacci(5) = {fibonacci(5)}")
print(f"Cache size: {len(fibonacci.cache)}")