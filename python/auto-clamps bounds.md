In Python, **list slicing never raises `IndexError` for out-of-range bounds**. This is deliberate language design.

### Key idea

Slicing uses the rule:

> “Take as many valid elements as possible within the requested range.”

So when you write:

```python
arr[:13]
```

Python interprets it as:

* start = 0 (default)
* end   = 13
* length = 10

Since only indices `0 … 9` exist, Python simply **clips** the slice to the valid range and returns everything available.

### Contrast with direct indexing

Indexing refers to a *single exact element*. If that element does not exist, that is an error:

```python
arr[13]   # raises IndexError
```

Slicing refers to a *range of elements*, and ranges can be partially valid.

### More examples

```python
arr[2:20]     # returns [3,4,5,6,7,8,9,10]
arr[20:]      # returns []
arr[-100:3]   # returns [1,2,3]
arr[:]        # returns full list
```

### Only cases where slicing errors

* Step = 0 is illegal:

```python
arr[::0]   # ValueError
```

* Otherwise, slice bounds never error.

### Why Python does this

* Convenience (common in high-level languages)
* Makes slicing safe and predictable
* Useful for algorithms where bounds may exceed limits

So you did not see “index out of range” because **Python slicing is tolerant and auto-clamps bounds**, while **element indexing is strict**.
