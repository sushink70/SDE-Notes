# Here are the ways to access values in Python's nested data structures:

## Nested Lists
# Use multiple square brackets with indices:

nested_list = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
print(nested_list[0][1])  # Output: 2
print(nested_list[2][0])  # Output: 7


## Nested Tuples
# Similar to lists, use multiple square brackets:

nested_tuple = ((1, 2, 3), (4, 5, 6), (7, 8, 9))
print(nested_tuple[1][2])  # Output: 6
print(nested_tuple[0][0])  # Output: 1


## Nested Arrays (NumPy)
# Use comma-separated indices or multiple brackets:

import numpy as np
nested_array = np.array([[1, 2, 3], [4, 5, 6]])
print(nested_array[0, 1])    # Output: 2 (preferred)
print(nested_array[0][1])    # Output: 2 (also works)


## Nested Sets
# Sets don't support indexing, but you can iterate or convert to list:

nested_set = {frozenset([1, 2]), frozenset([3, 4])}
# Convert to list to access by index
set_list = list(nested_set)
inner_set = list(set_list[0])  # Convert inner frozenset to list
print(inner_set[0])  # Access first element


## Nested Frozensets
# Similar to sets, no direct indexing:

nested_frozenset = frozenset([frozenset([1, 2]), frozenset([3, 4])])
# Convert to list for indexing
fs_list = list(nested_frozenset)
inner_list = list(fs_list[0])
print(inner_list[0])


## Nested Dictionaries
# Use multiple square brackets with keys:

nested_dict = {
    'level1': {
        'level2': {
            'value': 42
        }
    }
}
print(nested_dict['level1']['level2']['value'])  # Output: 42

# Safe access with get()
print(nested_dict.get('level1', {}).get('level2', {}).get('value'))


## Mixed Nested Structures

mixed = {
    'data': [
        {'name': 'Alice', 'scores': [85, 92, 78]},
        {'name': 'Bob', 'scores': [90, 88, 84]}
    ]
}
print(mixed['data'][0]['scores'][1])  # Output: 92


## Safe Access Techniques

# For safer access that handles missing keys/indices:


# Using try-except
try:
    value = nested_dict['key1']['key2']['key3']
except (KeyError, TypeError):
    value = None

# Using get() for dictionaries
value = nested_dict.get('key1', {}).get('key2', {}).get('key3')

# For lists with index checking
def safe_get(lst, *indices):
    for i in indices:
        try:
            lst = lst[i]
        except (IndexError, TypeError):
            return None
    return lst

result = safe_get(nested_list, 0, 1)  # Safely get nested_list[0][1]


# The key principle is that you chain the access operators (`[]` for indexing, `['key']` for dictionary keys) in the order of nesting depth.

# Here are more complex nested data structure access patterns:

## Deep Nesting with Mixed Types

complex_data = {
    'users': [
        {
            'id': 1,
            'profile': {
                'personal': {
                    'name': 'Alice',
                    'addresses': [
                        {'type': 'home', 'coords': (40.7128, -74.0060)},
                        {'type': 'work', 'coords': (40.7589, -73.9851)}
                    ]
                },
                'preferences': {
                    'notifications': {'email': True, 'sms': False},
                    'privacy': {'public_profile': False}
                }
            },
            'activity': {
                'recent_sessions': [
                    {'timestamp': '2024-01-15', 'actions': ['login', 'view_profile', 'logout']},
                    {'timestamp': '2024-01-14', 'actions': ['login', 'update_settings']}
                ]
            }
        }
    ],
    'metadata': {
        'version': '2.1',
        'schema': {
            'user_fields': frozenset(['id', 'profile', 'activity']),
            'required_fields': {'profile': ['personal', 'preferences']}
        }
    }
}

# Access Alice's work address coordinates
work_coords = complex_data['users'][0]['profile']['personal']['addresses'][1]['coords']
print(work_coords[0])  # Latitude: 40.7589

# Access recent session actions
recent_actions = complex_data['users'][0]['activity']['recent_sessions'][0]['actions']
print(recent_actions[1])  # 'view_profile'


## Nested Collections with Comprehensions

# 3D matrix as nested lists
matrix_3d = [
    [
        [1, 2, 3],
        [4, 5, 6]
    ],
    [
        [7, 8, 9],
        [10, 11, 12]
    ]
]

# Access and modify with comprehensions
# Get all middle elements from each 2D matrix
middle_elements = [matrix_3d[i][j][1] for i in range(len(matrix_3d)) 
                   for j in range(len(matrix_3d[i]))]
print(middle_elements)  # [2, 5, 8, 11]

# Create flattened version with coordinates
flattened_with_coords = [
    (i, j, k, matrix_3d[i][j][k]) 
    for i in range(len(matrix_3d))
    for j in range(len(matrix_3d[i]))
    for k in range(len(matrix_3d[i][j]))
]


## Advanced Dictionary Patterns

# Nested dictionaries with callable values and dynamic keys
config = {
    'database': {
        'connections': {
            'primary': {
                'host': 'localhost',
                'port': 5432,
                'auth': lambda: {'user': 'admin', 'pass': 'secret'}
            },
            'replica': {
                'host': 'replica.db.com',
                'port': 5432,
                'auth': lambda: {'user': 'readonly', 'pass': 'public'}
            }
        }
    },
    'cache': {
        'redis': {
            'clusters': {
                f'node_{i}': {
                    'host': f'redis-{i}.cluster.com',
                    'port': 6379 + i,
                    'config': {'maxmemory': f'{2**i}gb'}
                } for i in range(3)
            }
        }
    }
}

# Access with dynamic keys
node_key = 'node_1'
redis_config = config['cache']['redis']['clusters'][node_key]['config']
print(redis_config['maxmemory'])  # '2gb'

# Call nested function
auth_data = config['database']['connections']['primary']['auth']()
print(auth_data['user'])  # 'admin'


## Complex Nested Class Structures

class Node:
    def __init__(self, value, children=None):
        self.value = value
        self.children = children or {}
        self.metadata = {'created': '2024-01-01', 'access_count': 0}

# Create nested tree structure
root = Node('root', {
    'branch1': Node('b1', {
        'leaf1': Node('l1'),
        'leaf2': Node('l2', {
            'subleaf': Node('sl1')
        })
    }),
    'branch2': Node('b2', {
        'leaf3': Node('l3')
    })
})

# Access deep nested values
subleaf_value = root.children['branch1'].children['leaf2'].children['subleaf'].value
print(subleaf_value)  # 'sl1'

# Access with path traversal
def traverse_path(node, path):
    current = node
    for step in path:
        if hasattr(current, 'children') and step in current.children:
            current = current.children[step]
        else:
            return None
    return current

path = ['branch1', 'leaf2', 'subleaf']
result = traverse_path(root, path)
print(result.value if result else 'Not found')  # 'sl1'


## Advanced Safe Access Patterns

# Recursive safe getter
def deep_get(data, *keys, default=None):
    for key in keys:
        if isinstance(data, dict) and key in data:
            data = data[key]
        elif isinstance(data, (list, tuple)) and isinstance(key, int) and 0 <= key < len(data):
            data = data[key]
        elif hasattr(data, key):
            data = getattr(data, key)
        else:
            return default
    return data

# Usage examples
result1 = deep_get(complex_data, 'users', 0, 'profile', 'personal', 'name')
result2 = deep_get(complex_data, 'users', 0, 'nonexistent', 'key', default='N/A')
result3 = deep_get(root, 'children', 'branch1', 'children', 'leaf1', 'value')

# JSONPath-like access
def json_path_get(data, path_string):
    """
    Simple JSONPath-like access: 'users[0].profile.personal.name'
    """
    import re
    
    # Split by dots and handle array indices
    parts = re.split(r'\.|\[|\]', path_string)
    parts = [p for p in parts if p]  # Remove empty strings
    
    current = data
    for part in parts:
        if part.isdigit():
            current = current[int(part)]
        else:
            current = current[part]
    return current

# Usage
name = json_path_get(complex_data, 'users[0].profile.personal.name')
print(name)  # 'Alice'


## Nested Generators and Iterators

# Complex nested structure with generators
def nested_generator_data():
    return {
        'streams': {
            f'stream_{i}': {
                'data': (x**2 for x in range(j, j+3)),
                'metadata': {'size': 3, 'start': j}
            } for i, j in enumerate(range(0, 10, 3))
        }
    }

data = nested_generator_data()

# Access generator and consume values
stream_1_data = data['streams']['stream_1']['data']
values = list(stream_1_data)
print(values)  # [9, 16, 25] (3², 4², 5²)

# More complex: nested iterators with state
class StatefulNestedIterator:
    def __init__(self):
        self.data = {
            'sequences': {
                'fibonacci': self._fibonacci(),
                'primes': self._primes(),
                'squares': (x**2 for x in range(100))
            }
        }
    
    def _fibonacci(self):
        a, b = 0, 1
        while True:
            yield a
            a, b = b, a + b
    
    def _primes(self):
        def is_prime(n):
            return n > 1 and all(n % i != 0 for i in range(2, int(n**0.5) + 1))
        
        n = 2
        while True:
            if is_prime(n):
                yield n
            n += 1

# Usage
iterator_data = StatefulNestedIterator()
fib_gen = iterator_data.data['sequences']['fibonacci']
first_10_fibs = [next(fib_gen) for _ in range(10)]
print(first_10_fibs)  # [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]


## Multi-dimensional NumPy Arrays with Complex Indexing

import numpy as np

# 4D array: (batch, channels, height, width)
data_4d = np.random.rand(2, 3, 4, 5)

# Advanced indexing patterns
# Get all channels for first batch, middle rows
middle_channels = data_4d[0, :, 1:3, :]
print(middle_channels.shape)  # (3, 2, 5)

# Boolean indexing on nested conditions
mask = (data_4d[0, 0] > 0.5) & (data_4d[0, 1] < 0.3)
filtered_values = data_4d[0, 2][mask]

# Fancy indexing with multiple dimensions
batch_idx = [0, 1, 0]
channel_idx = [0, 1, 2]
height_idx = [0, 1, 2]
width_idx = [0, 1, 2]
selected_values = data_4d[batch_idx, channel_idx, height_idx, width_idx]


## Dynamic Nested Access with Decorators

def nested_access_logger(func):
    def wrapper(*args, **kwargs):
        print(f"Accessing nested structure with path: {args[1:]}")
        try:
            result = func(*args, **kwargs)
            print(f"Successfully retrieved: {result}")
            return result
        except Exception as e:
            print(f"Access failed: {e}")
            return None
    return wrapper

@nested_access_logger
def safe_nested_access(data, *path):
    current = data
    for key in path:
        if isinstance(current, dict):
            current = current[key]
        elif isinstance(current, (list, tuple)):
            current = current[int(key)]
        else:
            current = getattr(current, key)
    return current

# Usage with logging
result = safe_nested_access(complex_data, 'users', 0, 'profile', 'personal', 'name')


# These examples show increasingly sophisticated ways to work with nested data structures, including error handling, dynamic access patterns, generators, multi-dimensional arrays, and custom access methods.