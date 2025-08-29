# Python Tricks

If you got a variable, check it's properties depending on the variable like, type(int or string or float or boolean), size(memory, int value), len(array, strings), hight (in tree dsa), count,

you can use,
len(), type(), id(), sys.getsizeof(), isinstance(), callable(), dir(), vars(), locals(), globals(), help(), hasattr(), getattr(), setattr(), delattr(), issubclass(), isintance(), issubclass(), isinstance(),
< > == !=, in, not in, is, is not, and, or, not, &, |, ^, ~, <<, >>, +, -, *, /, //, %, **, <, >, <=, >=, ==, !=, +=, -=,*=, /=, //=, %=,**=, &, |=, ^=, <<=, >>=,
int, float, complex, bool, str, list, tuple, set, dict, frozenset, bytes, bytearray, memoryview, range, None, Ellipsis, NotImplemented



To check if an object is sized (i.e., supports len()), you can:

1. Use hasattr(obj, "__len__")

```python
if hasattr(obj, "__len__"):
    print("Object is sized (supports len())")
else:
    print("Object is not sized")
```

2. Use collections.abc.Sized (Pythonic way)

```python
from collections.abc import Sized

if isinstance(obj, Sized):
    print("Object is sized")
else:
    print("Object is not sized")
```

Both methods work, but using collections.abc.Sized is more idiomatic in modern Python.

