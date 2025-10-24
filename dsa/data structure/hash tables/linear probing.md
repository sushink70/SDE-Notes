# Comprehensive Guide to Linear Probing

Linear probing is a collision resolution technique used in hash tables. When a collision occurs (two keys hash to the same index), linear probing searches sequentially through the table until an empty slot is found.

## How Linear Probing Works

1. **Hash Function**: Compute `index = hash(key) % table_size`
2. **Collision Resolution**: If the slot is occupied, check `(index + 1) % table_size`, then `(index + 2) % table_size`, and so on
3. **Clustering**: Keys tend to cluster together, which can degrade performance

## Key Concepts

- **Load Factor (α)**: ratio of filled slots to total slots. Keep α < 0.7 for good performance
- **Primary Clustering**: Consecutive occupied slots form clusters, increasing search time
- **Tombstones**: Markers for deleted entries to maintain probe sequences
- **Rehashing**: Resize and rebuild the table when load factor gets too high

## Time Complexity

- **Average Case** (α < 0.7):
  - Insert: O(1)
  - Search: O(1)
  - Delete: O(1)

- **Worst Case** (high load factor or clustering):
  - All operations: O(n)

## Implementation in Rust
```rust
use std::collections::hash_map::DefaultHasher;
use std::hash::{Hash, Hasher};

#[derive(Clone, Debug)]
enum Slot<K, V> {
    Empty,
    Occupied(K, V),
    Tombstone,
}

pub struct LinearProbingHashTable<K, V> {
    table: Vec<Slot<K, V>>,
    size: usize,
    capacity: usize,
}

impl<K: Hash + Eq + Clone, V: Clone> LinearProbingHashTable<K, V> {
    pub fn new(capacity: usize) -> Self {
        let cap = capacity.max(16);
        Self {
            table: (0..cap).map(|_| Slot::Empty).collect(),
            size: 0,
            capacity: cap,
        }
    }

    fn hash(&self, key: &K) -> usize {
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        (hasher.finish() as usize) % self.capacity
    }

    fn load_factor(&self) -> f64 {
        self.size as f64 / self.capacity as f64
    }

    fn resize(&mut self) {
        let new_capacity = self.capacity * 2;
        let old_table = std::mem::replace(
            &mut self.table,
            (0..new_capacity).map(|_| Slot::Empty).collect(),
        );
        
        self.capacity = new_capacity;
        self.size = 0;

        for slot in old_table {
            if let Slot::Occupied(k, v) = slot {
                self.insert(k, v);
            }
        }
    }

    pub fn insert(&mut self, key: K, value: V) -> Option<V> {
        if self.load_factor() > 0.7 {
            self.resize();
        }

        let mut idx = self.hash(&key);
        let start_idx = idx;

        loop {
            match &self.table[idx] {
                Slot::Empty | Slot::Tombstone => {
                    self.table[idx] = Slot::Occupied(key, value);
                    self.size += 1;
                    return None;
                }
                Slot::Occupied(k, _) if k == &key => {
                    if let Slot::Occupied(_, old_val) = 
                        std::mem::replace(&mut self.table[idx], Slot::Occupied(key, value)) {
                        return Some(old_val);
                    }
                    return None;
                }
                _ => {
                    idx = (idx + 1) % self.capacity;
                    if idx == start_idx {
                        self.resize();
                        return self.insert(key, value);
                    }
                }
            }
        }
    }

    pub fn get(&self, key: &K) -> Option<&V> {
        let mut idx = self.hash(key);
        let start_idx = idx;

        loop {
            match &self.table[idx] {
                Slot::Empty => return None,
                Slot::Occupied(k, v) if k == key => return Some(v),
                _ => {
                    idx = (idx + 1) % self.capacity;
                    if idx == start_idx {
                        return None;
                    }
                }
            }
        }
    }

    pub fn remove(&mut self, key: &K) -> Option<V> {
        let mut idx = self.hash(key);
        let start_idx = idx;

        loop {
            match &self.table[idx] {
                Slot::Empty => return None,
                Slot::Occupied(k, _) if k == key => {
                    if let Slot::Occupied(_, v) = 
                        std::mem::replace(&mut self.table[idx], Slot::Tombstone) {
                        self.size -= 1;
                        return Some(v);
                    }
                    return None;
                }
                _ => {
                    idx = (idx + 1) % self.capacity;
                    if idx == start_idx {
                        return None;
                    }
                }
            }
        }
    }

    pub fn len(&self) -> usize {
        self.size
    }

    pub fn is_empty(&self) -> bool {
        self.size == 0
    }
}

fn main() {
    let mut ht = LinearProbingHashTable::new(10);
    
    // Insert operations
    ht.insert("apple", 5);
    ht.insert("banana", 7);
    ht.insert("cherry", 3);
    ht.insert("date", 12);
    
    println!("Size: {}", ht.len());
    
    // Get operations
    if let Some(val) = ht.get(&"apple") {
        println!("apple: {}", val);
    }
    
    if let Some(val) = ht.get(&"banana") {
        println!("banana: {}", val);
    }
    
    // Update operation
    if let Some(old) = ht.insert("apple", 10) {
        println!("Updated apple from {} to 10", old);
    }
    
    // Remove operation
    if let Some(val) = ht.remove(&"cherry") {
        println!("Removed cherry: {}", val);
    }
    
    println!("Final size: {}", ht.len());
    
    // Non-existent key
    match ht.get(&"grape") {
        Some(_) => println!("Found grape"),
        None => println!("grape not found"),
    }
}
```

## Implementation in Python
```python
class Slot:
    """Represents a slot in the hash table"""
    EMPTY = 0
    OCCUPIED = 1
    TOMBSTONE = 2
    
    def __init__(self, status=None, key=None, value=None):
        self.status = status if status is not None else Slot.EMPTY
        self.key = key
        self.value = value


class LinearProbingHashTable:
    """Hash table implementation using linear probing for collision resolution"""
    
    def __init__(self, capacity=16):
        self.capacity = max(capacity, 16)
        self.table = [Slot() for _ in range(self.capacity)]
        self.size = 0
    
    def _hash(self, key):
        """Compute hash index for a key"""
        return hash(key) % self.capacity
    
    def _load_factor(self):
        """Calculate current load factor"""
        return self.size / self.capacity
    
    def _resize(self):
        """Resize the table when load factor exceeds threshold"""
        old_table = self.table
        self.capacity *= 2
        self.table = [Slot() for _ in range(self.capacity)]
        self.size = 0
        
        # Rehash all existing items
        for slot in old_table:
            if slot.status == Slot.OCCUPIED:
                self.insert(slot.key, slot.value)
    
    def insert(self, key, value):
        """Insert or update a key-value pair"""
        if self._load_factor() > 0.7:
            self._resize()
        
        idx = self._hash(key)
        start_idx = idx
        
        while True:
            slot = self.table[idx]
            
            # Found empty slot or tombstone - insert here
            if slot.status in (Slot.EMPTY, Slot.TOMBSTONE):
                self.table[idx] = Slot(Slot.OCCUPIED, key, value)
                self.size += 1
                return None
            
            # Key already exists - update value
            if slot.status == Slot.OCCUPIED and slot.key == key:
                old_value = slot.value
                slot.value = value
                return old_value
            
            # Continue probing
            idx = (idx + 1) % self.capacity
            
            # Table is full (shouldn't happen with proper resizing)
            if idx == start_idx:
                self._resize()
                return self.insert(key, value)
    
    def get(self, key):
        """Retrieve value for a key, or None if not found"""
        idx = self._hash(key)
        start_idx = idx
        
        while True:
            slot = self.table[idx]
            
            # Empty slot means key doesn't exist
            if slot.status == Slot.EMPTY:
                return None
            
            # Found the key
            if slot.status == Slot.OCCUPIED and slot.key == key:
                return slot.value
            
            # Continue probing
            idx = (idx + 1) % self.capacity
            
            # Wrapped around - key not found
            if idx == start_idx:
                return None
    
    def remove(self, key):
        """Remove a key-value pair and return the value"""
        idx = self._hash(key)
        start_idx = idx
        
        while True:
            slot = self.table[idx]
            
            # Empty slot means key doesn't exist
            if slot.status == Slot.EMPTY:
                return None
            
            # Found the key - mark as tombstone
            if slot.status == Slot.OCCUPIED and slot.key == key:
                value = slot.value
                slot.status = Slot.TOMBSTONE
                slot.key = None
                slot.value = None
                self.size -= 1
                return value
            
            # Continue probing
            idx = (idx + 1) % self.capacity
            
            # Wrapped around - key not found
            if idx == start_idx:
                return None
    
    def __len__(self):
        return self.size
    
    def __contains__(self, key):
        return self.get(key) is not None
    
    def __getitem__(self, key):
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value
    
    def __setitem__(self, key, value):
        self.insert(key, value)
    
    def __delitem__(self, key):
        if self.remove(key) is None:
            raise KeyError(key)


# Example usage
if __name__ == "__main__":
    ht = LinearProbingHashTable(capacity=10)
    
    # Insert operations
    ht["apple"] = 5
    ht["banana"] = 7
    ht["cherry"] = 3
    ht.insert("date", 12)
    
    print(f"Size: {len(ht)}")
    
    # Get operations
    print(f"apple: {ht['apple']}")
    print(f"banana: {ht.get('banana')}")
    
    # Check existence
    print(f"'cherry' in table: {'cherry' in ht}")
    
    # Update operation
    old_value = ht.insert("apple", 10)
    print(f"Updated apple from {old_value} to {ht['apple']}")
    
    # Remove operation
    removed = ht.remove("cherry")
    print(f"Removed cherry: {removed}")
    
    print(f"Final size: {len(ht)}")
    
    # Non-existent key
    result = ht.get("grape")
    print(f"grape: {result}")
    
    # Test with collisions
    print("\nTesting collision handling:")
    ht2 = LinearProbingHashTable(capacity=8)
    for i in range(15):
        ht2[f"key{i}"] = i * 10
    
    print(f"Inserted 15 items, capacity: {ht2.capacity}, size: {len(ht2)}")
```

## Implementation in Go
```go
package main

import (
	"fmt"
	"hash/fnv"
)

// SlotStatus represents the state of a hash table slot
type SlotStatus int

const (
	Empty SlotStatus = iota
	Occupied
	Tombstone
)

// Slot represents a single slot in the hash table
type Slot struct {
	status SlotStatus
	key    string
	value  interface{}
}

// LinearProbingHashTable implements a hash table using linear probing
type LinearProbingHashTable struct {
	table    []Slot
	size     int
	capacity int
}

// NewLinearProbingHashTable creates a new hash table with given capacity
func NewLinearProbingHashTable(capacity int) *LinearProbingHashTable {
	if capacity < 16 {
		capacity = 16
	}
	return &LinearProbingHashTable{
		table:    make([]Slot, capacity),
		size:     0,
		capacity: capacity,
	}
}

// hash computes the hash index for a key
func (ht *LinearProbingHashTable) hash(key string) int {
	h := fnv.New32a()
	h.Write([]byte(key))
	return int(h.Sum32()) % ht.capacity
}

// loadFactor calculates the current load factor
func (ht *LinearProbingHashTable) loadFactor() float64 {
	return float64(ht.size) / float64(ht.capacity)
}

// resize doubles the capacity and rehashes all items
func (ht *LinearProbingHashTable) resize() {
	oldTable := ht.table
	ht.capacity *= 2
	ht.table = make([]Slot, ht.capacity)
	ht.size = 0

	// Rehash all occupied slots
	for _, slot := range oldTable {
		if slot.status == Occupied {
			ht.Insert(slot.key, slot.value)
		}
	}
}

// Insert adds or updates a key-value pair
func (ht *LinearProbingHashTable) Insert(key string, value interface{}) interface{} {
	if ht.loadFactor() > 0.7 {
		ht.resize()
	}

	idx := ht.hash(key)
	startIdx := idx

	for {
		slot := &ht.table[idx]

		// Found empty slot or tombstone - insert here
		if slot.status == Empty || slot.status == Tombstone {
			ht.table[idx] = Slot{
				status: Occupied,
				key:    key,
				value:  value,
			}
			ht.size++
			return nil
		}

		// Key already exists - update value
		if slot.status == Occupied && slot.key == key {
			oldValue := slot.value
			slot.value = value
			return oldValue
		}

		// Continue probing
		idx = (idx + 1) % ht.capacity

		// Table is full (shouldn't happen with proper resizing)
		if idx == startIdx {
			ht.resize()
			return ht.Insert(key, value)
		}
	}
}

// Get retrieves the value for a key
func (ht *LinearProbingHashTable) Get(key string) (interface{}, bool) {
	idx := ht.hash(key)
	startIdx := idx

	for {
		slot := &ht.table[idx]

		// Empty slot means key doesn't exist
		if slot.status == Empty {
			return nil, false
		}

		// Found the key
		if slot.status == Occupied && slot.key == key {
			return slot.value, true
		}

		// Continue probing
		idx = (idx + 1) % ht.capacity

		// Wrapped around - key not found
		if idx == startIdx {
			return nil, false
		}
	}
}

// Remove deletes a key-value pair
func (ht *LinearProbingHashTable) Remove(key string) (interface{}, bool) {
	idx := ht.hash(key)
	startIdx := idx

	for {
		slot := &ht.table[idx]

		// Empty slot means key doesn't exist
		if slot.status == Empty {
			return nil, false
		}

		// Found the key - mark as tombstone
		if slot.status == Occupied && slot.key == key {
			value := slot.value
			slot.status = Tombstone
			slot.key = ""
			slot.value = nil
			ht.size--
			return value, true
		}

		// Continue probing
		idx = (idx + 1) % ht.capacity

		// Wrapped around - key not found
		if idx == startIdx {
			return nil, false
		}
	}
}

// Size returns the number of elements
func (ht *LinearProbingHashTable) Size() int {
	return ht.size
}

// IsEmpty checks if the table is empty
func (ht *LinearProbingHashTable) IsEmpty() bool {
	return ht.size == 0
}

// Contains checks if a key exists
func (ht *LinearProbingHashTable) Contains(key string) bool {
	_, found := ht.Get(key)
	return found
}

func main() {
	ht := NewLinearProbingHashTable(10)

	// Insert operations
	ht.Insert("apple", 5)
	ht.Insert("banana", 7)
	ht.Insert("cherry", 3)
	ht.Insert("date", 12)

	fmt.Printf("Size: %d\n", ht.Size())

	// Get operations
	if val, found := ht.Get("apple"); found {
		fmt.Printf("apple: %v\n", val)
	}

	if val, found := ht.Get("banana"); found {
		fmt.Printf("banana: %v\n", val)
	}

	// Check existence
	fmt.Printf("'cherry' exists: %v\n", ht.Contains("cherry"))

	// Update operation
	if oldVal := ht.Insert("apple", 10); oldVal != nil {
		fmt.Printf("Updated apple from %v to 10\n", oldVal)
	}

	// Remove operation
	if val, removed := ht.Remove("cherry"); removed {
		fmt.Printf("Removed cherry: %v\n", val)
	}

	fmt.Printf("Final size: %d\n", ht.Size())

	// Non-existent key
	if val, found := ht.Get("grape"); found {
		fmt.Printf("grape: %v\n", val)
	} else {
		fmt.Println("grape not found")
	}

	// Test collision handling
	fmt.Println("\nTesting collision handling:")
	ht2 := NewLinearProbingHashTable(8)
	for i := 0; i < 15; i++ {
		ht2.Insert(fmt.Sprintf("key%d", i), i*10)
	}
	fmt.Printf("Inserted 15 items, capacity: %d, size: %d\n", ht2.capacity, ht2.Size())
}
```
## Key Implementation Details

### 1. **Slot States**
All three implementations use three states:
- **Empty**: Never been used
- **Occupied**: Currently holds a key-value pair
- **Tombstone**: Previously occupied but now deleted (maintains probe sequences)

### 2. **Hash Function**
- **Rust**: Uses `DefaultHasher` from std library
- **Python**: Uses built-in `hash()` function
- **Go**: Uses FNV-1a hash algorithm

### 3. **Collision Resolution**
When collision occurs at index `i`:
```
next_index = (i + 1) % capacity
```

### 4. **Dynamic Resizing**
- Triggered when load factor > 0.7
- Doubles capacity
- Rehashes all existing entries
- Tombstones are not carried over

### 5. **Tombstone Strategy**
Tombstones are crucial because:
- They maintain probe sequences for existing keys
- Without them, searches would terminate prematurely
- They're replaced during insertions

## Performance Characteristics

| Load Factor | Avg Probes (Search) | Avg Probes (Insert) |
|-------------|---------------------|---------------------|
| 0.5         | 1.5                 | 2.5                 |
| 0.7         | 2.2                 | 5.0                 |
| 0.9         | 5.5                 | 50.5                |

## Advantages vs Disadvantages

**Advantages:**
- Simple implementation
- Good cache locality (sequential memory access)
- No extra memory for pointers (unlike chaining)

**Disadvantages:**
- Primary clustering degrades performance
- Performance degrades with high load factors
- Deletion requires tombstones
- Resizing is expensive

## Best Practices

1. **Keep load factor below 0.7** for optimal performance
2. **Use good hash functions** to minimize initial collisions
3. **Consider tombstone cleanup** during resizing
4. **Choose initial capacity wisely** based on expected size
5. **Consider alternatives** (quadratic probing, double hashing) for specific use cases