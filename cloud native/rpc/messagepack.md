# MessagePack: A Complete, In-Depth Guide
### From Fundamentals to Production — Linux · Polyglot · Redis · Go

---

> **Mental Model Before You Begin:**
> Think of data serialization as **translation**. When a Go program wants to talk
> to a Python service or store data in Redis, it must convert its in-memory
> structures into a universal language. MessagePack is that language — but unlike
> JSON (text-based), MessagePack speaks in **pure binary**, making it faster,
> smaller, and more precise.

---

## Table of Contents

```
1.  Foundations — What is Serialization?
2.  What is MessagePack?
3.  Why MessagePack? (vs JSON, XML, Protobuf, CBOR)
4.  The MessagePack Type System
5.  Binary Encoding Deep Dive
6.  Format Specification — Byte-Level Anatomy
7.  Go Implementation — From Zero to Expert
8.  Polyglot Communication (Go ↔ Python ↔ Node ↔ Rust)
9.  MessagePack on Linux — System-Level Concepts
10. MessagePack + Redis
11. Streaming & Large Payloads
12. Extension Types (Custom Types)
13. Schema Evolution & Versioning
14. Performance Benchmarks & Optimization
15. Error Handling & Debugging
16. Decision Trees & Mental Models
17. Summary Cheatsheet
```

---

## 1. Foundations — What is Serialization?

### 1.1 The Problem

Imagine you have this Go struct in memory:

```
RAM Layout (Go process)
┌─────────────────────────────────────────┐
│  struct User {                          │
│    Name: "Alice"  → pointer → [65,108,  │
│                                105,99,  │
│                                101]     │
│    Age:  30       → int64 → 0x1E        │
│    Active: true   → bool → 0x01         │
│  }                                      │
└─────────────────────────────────────────┘
         │
         │ How do you send this over a network?
         │ How do you store this in Redis?
         │ How does Python read this?
         ▼
    [ SERIALIZATION ]
```

**Serialization** = Converting an in-memory data structure into a flat sequence of bytes that can be:
- Sent over a network (TCP, HTTP, gRPC)
- Stored on disk or in a database
- Read by another process or language

**Deserialization** = The reverse — reading bytes and reconstructing the data structure.

### 1.2 Serialization Formats

```
FORMAT TAXONOMY
═══════════════════════════════════════════════════════════════
 Text-Based            │  Binary-Based
───────────────────────┼───────────────────────────────────────
 JSON    {"age": 30}   │  MessagePack  [82 A3 61 67 65 1E ...]
 XML     <age>30</age> │  Protobuf     [0A 05 41 6C 69 63 65 ...]
 YAML    age: 30       │  CBOR         [A1 63 61 67 65 18 1E ...]
 TOML    age = 30      │  Avro         [binary w/ schema]
 CSV     30,...        │  Thrift       [binary frames]
───────────────────────┼───────────────────────────────────────
 Human-readable        │  Machine-optimized
 Larger size           │  Smaller size
 Slower parse          │  Faster parse
 No types (strings)    │  Rich type system
═══════════════════════════════════════════════════════════════
```

---

## 2. What is MessagePack?

**MessagePack** (also written as **msgpack**) is a binary serialization format created by **Sadayuki Furuhashi** in 2008. Its tagline:

> *"It's like JSON, but fast and small."*

### 2.1 Core Philosophy

```
JSON:  {"name":"Alice","age":30,"active":true}
        ↑ 39 bytes, all ASCII text

msgpack: 83 A4 6E 61 6D 65 A5 41 6C 69 63 65 A3 61 67 65 1E A6 61 63 74 69 76 65 C3
         ↑ 25 bytes, binary — 35% smaller!
```

### 2.2 Design Goals

```
┌─────────────────────────────────────────────────────────────┐
│                   MESSAGEPACK DESIGN GOALS                  │
├─────────────────────────────────────────────────────────────┤
│  1. COMPACT     → Smaller than JSON, saves bandwidth/memory │
│  2. FAST        → Minimal parsing overhead                  │
│  3. COMPATIBLE  → Works across 50+ languages                │
│  4. TYPED       → Integers stay integers (not "30" string)  │
│  5. SCHEMA-FREE → No .proto or .thrift file needed          │
│  6. STREAMABLE  → Parse incrementally, don't need full buf  │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Why MessagePack? — Comparative Analysis

### 3.1 The Comparison Matrix

```
╔══════════════╦═══════╦══════════╦═══════════╦══════╦══════╗
║ Feature      ║ JSON  ║ MsgPack  ║ Protobuf  ║ CBOR ║ Avro ║
╠══════════════╬═══════╬══════════╬═══════════╬══════╬══════╣
║ Size         ║ Large ║ Small    ║ Smallest  ║ Small║ Small║
║ Speed        ║ Slow  ║ Fast     ║ Fastest   ║ Fast ║ Fast ║
║ Human-Read   ║  ✓    ║  ✗       ║  ✗        ║  ✗   ║  ✗   ║
║ Schema       ║ None  ║ Optional ║ Required  ║ None ║ Reqd ║
║ Languages    ║  50+  ║  50+     ║  30+      ║  20+ ║  15+ ║
║ Self-Descr.  ║  ✓    ║  ✓       ║  ✗        ║  ✓   ║  ✗   ║
║ Streaming    ║  Hard ║  Easy    ║  Medium   ║  Easy║ Hard ║
║ Null support ║  ✓    ║  ✓       ║  Tricky   ║  ✓   ║  ✓   ║
║ Binary data  ║  B64  ║  Native  ║  Native   ║  Nat.║ Nat. ║
╚══════════════╩═══════╩══════════╩═══════════╩══════╩══════╝
```

**Key Insight:**
- Use **JSON** when humans need to read it (config files, APIs that need debugging)
- Use **MessagePack** when you control both ends + need speed/size (microservices, caching, queues)
- Use **Protobuf** when you need maximum performance + schema enforcement
- Use **Avro** for Kafka / big data pipelines with schema registry

### 3.2 When NOT to Use MessagePack

```
DECISION TREE: Should I use MessagePack?
═══════════════════════════════════════════════════════════════

  Do humans need to read the data directly?
           │
    YES ───┼─── NO
           │         │
      Use JSON       Do you need strict schema enforcement?
                              │
                      YES ────┼──── NO
                              │          │
                         Protobuf    Do you need
                         or Thrift   cross-language?
                                          │
                                   YES ───┼─── NO
                                          │        │
                                     MessagePack  Go gob /
                                     or CBOR      custom binary
```

---

## 4. The MessagePack Type System

### 4.1 All Supported Types

```
MESSAGEPACK TYPE HIERARCHY
═══════════════════════════════════════════════════════════════

  MessagePack Value
  ├── Nil          → null / None / nil
  ├── Boolean      → true / false
  ├── Integer
  │   ├── Signed   → int8, int16, int32, int64
  │   └── Unsigned → uint8, uint16, uint32, uint64
  ├── Float
  │   ├── Float32  → IEEE 754 single precision
  │   └── Float64  → IEEE 754 double precision
  ├── String       → UTF-8 encoded text
  ├── Binary       → raw bytes (not text)
  ├── Array        → ordered sequence of values
  ├── Map          → key-value pairs (like dict/object)
  └── Extension    → custom application-defined types
      ├── Timestamp (built-in ext type -1)
      └── User-defined (ext types 0–127)
```

### 4.2 Type Mapping Across Languages

```
╔══════════════╦══════════════╦══════════════╦══════════════╗
║ MsgPack      ║ Go           ║ Python       ║ Rust         ║
╠══════════════╬══════════════╬══════════════╬══════════════╣
║ nil          ║ nil          ║ None         ║ Option::None ║
║ bool         ║ bool         ║ bool         ║ bool         ║
║ int (signed) ║ int64        ║ int          ║ i64          ║
║ uint         ║ uint64       ║ int          ║ u64          ║
║ float32      ║ float32      ║ float        ║ f32          ║
║ float64      ║ float64      ║ float        ║ f64          ║
║ str          ║ string       ║ str          ║ String       ║
║ bin          ║ []byte       ║ bytes        ║ Vec<u8>      ║
║ array        ║ []interface{}║ list         ║ Vec<Value>   ║
║ map          ║ map[string]..║ dict         ║ HashMap      ║
║ ext          ║ custom       ║ custom       ║ custom       ║
╚══════════════╩══════════════╩══════════════╩══════════════╝
```

---

## 5. Binary Encoding Deep Dive

### 5.1 Concept: Format Byte (Tag Byte)

Every MessagePack value begins with a **format byte** — a single byte that tells the decoder:
1. What TYPE this value is
2. Sometimes, the VALUE itself (for small numbers/strings)

```
FORMAT BYTE STRUCTURE
═══════════════════════════════════════════════════════════════

  Byte: 1000 0011  (0x83)
        ────┬────
            │
            └─ High 4 bits: 1000 = fixmap format
               Low 4 bits:  0011 = 3 elements in map
                                   (value encoded IN the byte!)

This is "fixmap with 3 elements" — the entire header is 1 byte!
Compare to JSON: you need { and count elements while parsing.
```

### 5.2 Format Byte Table

```
╔═══════════════╦═══════════════╦══════════════════════════════╗
║ Format Name   ║ Byte Range    ║ Description                  ║
╠═══════════════╬═══════════════╬══════════════════════════════╣
║ positive fixint║ 0x00 - 0x7F  ║ Integer 0–127 (1 byte total) ║
║ fixmap        ║ 0x80 - 0x8F   ║ Map with 0–15 elements       ║
║ fixarray      ║ 0x90 - 0x9F   ║ Array with 0–15 elements     ║
║ fixstr        ║ 0xA0 - 0xBF   ║ String with 0–31 bytes       ║
║ nil           ║ 0xC0          ║ null value                   ║
║ (never used)  ║ 0xC1          ║ Reserved                     ║
║ false         ║ 0xC2          ║ Boolean false                ║
║ true          ║ 0xC3          ║ Boolean true                 ║
║ bin8          ║ 0xC4          ║ Binary, up to 255 bytes      ║
║ bin16         ║ 0xC5          ║ Binary, up to 65535 bytes    ║
║ bin32         ║ 0xC6          ║ Binary, up to 4GB            ║
║ ext8          ║ 0xC7          ║ Extension, up to 255 bytes   ║
║ ext16         ║ 0xC8          ║ Extension, up to 65535 bytes ║
║ ext32         ║ 0xC9          ║ Extension, up to 4GB         ║
║ float32       ║ 0xCA          ║ IEEE 754 float32             ║
║ float64       ║ 0xCB          ║ IEEE 754 float64             ║
║ uint8         ║ 0xCC          ║ Unsigned 8-bit int           ║
║ uint16        ║ 0xCD          ║ Unsigned 16-bit int          ║
║ uint32        ║ 0xCE          ║ Unsigned 32-bit int          ║
║ uint64        ║ 0xCF          ║ Unsigned 64-bit int          ║
║ int8          ║ 0xD0          ║ Signed 8-bit int             ║
║ int16         ║ 0xD1          ║ Signed 16-bit int            ║
║ int32         ║ 0xD2          ║ Signed 32-bit int            ║
║ int64         ║ 0xD3          ║ Signed 64-bit int            ║
║ fixext1       ║ 0xD4          ║ Extension, exactly 1 byte   ║
║ fixext2       ║ 0xD5          ║ Extension, exactly 2 bytes  ║
║ fixext4       ║ 0xD6          ║ Extension, exactly 4 bytes  ║
║ fixext8       ║ 0xD7          ║ Extension, exactly 8 bytes  ║
║ fixext16      ║ 0xD8          ║ Extension, exactly 16 bytes ║
║ str8          ║ 0xD9          ║ String, up to 255 bytes      ║
║ str16         ║ 0xDA          ║ String, up to 65535 bytes    ║
║ str32         ║ 0xDB          ║ String, up to 4GB            ║
║ array16       ║ 0xDC          ║ Array with up to 65535 items ║
║ array32       ║ 0xDD          ║ Array with up to 4GB items   ║
║ map16         ║ 0xDE          ║ Map with up to 65535 pairs   ║
║ map32         ║ 0xDF          ║ Map with up to 4GB pairs     ║
║ negative fixint║ 0xE0 - 0xFF  ║ Integer -32 to -1            ║
╚═══════════════╩═══════════════╩══════════════════════════════╝
```

### 5.3 Encoding Examples — Byte by Byte

#### Example 1: Encoding integer 42

```
Value: 42 (fits in 0–127 range → positive fixint)

  Byte:   0x2A
          ────
          │
          └─ 42 in hex = 0x2A
             The value IS the byte! No type tag needed!
             Because 42 ≤ 127, format byte = value byte.

JSON:       "42"  → 2 bytes
MessagePack: 2A   → 1 byte  (50% smaller!)
```

#### Example 2: Encoding integer 200

```
Value: 200 (doesn't fit in positive fixint, needs uint8)

  Byte 0:  0xCC  → "uint8 follows"
  Byte 1:  0xC8  → 200 in hex

Total: 2 bytes

JSON:       "200"  → 3 bytes
MessagePack: CC C8 → 2 bytes
```

#### Example 3: Encoding string "Hi"

```
Value: "Hi" (2 bytes, fits in fixstr: 0–31 bytes)

  Byte 0:  0xA2   → fixstr with length 2
                     (0xA0 | 0x02 = 0xA2)
                      ↑ fixstr base  ↑ length in lower bits
  Byte 1:  0x48   → 'H' (ASCII 72)
  Byte 2:  0x69   → 'i' (ASCII 105)

Total: 3 bytes

JSON:       "\"Hi\""  → 4 bytes (with quotes)
MessagePack: A2 48 69 → 3 bytes
```

#### Example 4: Encoding {"name": "Alice", "age": 30}

```
STEP-BY-STEP ENCODING

  Map has 2 entries → fixmap (0x80 | 0x02 = 0x82)

  Byte 0:  0x82   → fixmap, 2 elements

  Key "name" → fixstr(4) = 0xA4 + "name" bytes
  Byte 1:  0xA4   → fixstr length 4
  Byte 2:  0x6E   → 'n'
  Byte 3:  0x61   → 'a'
  Byte 4:  0x6D   → 'm'
  Byte 5:  0x65   → 'e'

  Value "Alice" → fixstr(5) = 0xA5 + "Alice" bytes
  Byte 6:  0xA5   → fixstr length 5
  Byte 7:  0x41   → 'A'
  Byte 8:  0x6C   → 'l'
  Byte 9:  0x69   → 'i'
  Byte 10: 0x63   → 'c'
  Byte 11: 0x65   → 'e'

  Key "age" → fixstr(3) = 0xA3 + "age" bytes
  Byte 12: 0xA3   → fixstr length 3
  Byte 13: 0x61   → 'a'
  Byte 14: 0x67   → 'g'
  Byte 15: 0x65   → 'e'

  Value 30 → positive fixint (30 ≤ 127)
  Byte 16: 0x1E   → 30 in hex

  TOTAL: 17 bytes

  JSON: {"name":"Alice","age":30} = 27 bytes
  Savings: ~37%

  VISUAL:
  ┌────┬────┬────┬────┬────┬────┬────┬────┬────┐
  │ 82 │ A4 │ 6E │ 61 │ 6D │ 65 │ A5 │ 41 │ 6C │
  └────┴────┴────┴────┴────┴────┴────┴────┴────┘
  map2  str4  n    a    m    e   str5  A    l

  ┌────┬────┬────┬────┬────┬────┬────┬────┐
  │ 69 │ 63 │ 65 │ A3 │ 61 │ 67 │ 65 │ 1E │
  └────┴────┴────┴────┴────┴────┴────┴────┘
   i    c    e   str3  a    g    e    30
```

---

## 6. Format Specification — Byte-Level Anatomy

### 6.1 Integer Encoding Strategy

MessagePack uses **variable-length encoding** for integers — the encoder always chooses the smallest format:

```
INTEGER ENCODING FLOW
═══════════════════════════════════════════════════════════════

  Input Integer N
        │
        ├── 0 ≤ N ≤ 127          → positive fixint (1 byte)
        │
        ├── -32 ≤ N ≤ -1         → negative fixint (1 byte)
        │                           (range E0..FF)
        ├── 0 ≤ N ≤ 255          → uint8  (2 bytes: CC + byte)
        │
        ├── 0 ≤ N ≤ 65535        → uint16 (3 bytes: CD + 2 bytes)
        │
        ├── 0 ≤ N ≤ 4294967295   → uint32 (5 bytes: CE + 4 bytes)
        │
        ├── 0 ≤ N ≤ 2^64-1       → uint64 (9 bytes: CF + 8 bytes)
        │
        ├── -128 ≤ N ≤ 127       → int8   (2 bytes: D0 + byte)
        │
        ├── -32768 ≤ N ≤ 32767   → int16  (3 bytes: D1 + 2 bytes)
        │
        ├── -2^31 ≤ N ≤ 2^31-1   → int32  (5 bytes: D2 + 4 bytes)
        │
        └── -2^63 ≤ N ≤ 2^63-1   → int64  (9 bytes: D3 + 8 bytes)

NOTE: Encoders should use UNSIGNED formats for positive numbers
      and pick the SMALLEST format that fits the value.
```

### 6.2 String Encoding Strategy

```
STRING ENCODING FLOW
═══════════════════════════════════════════════════════════════

  String of length L
        │
        ├── L ≤ 31      → fixstr (1 byte header: 0xA0 | L)
        │
        ├── L ≤ 255     → str8  (2 byte header: D9 + L as uint8)
        │
        ├── L ≤ 65535   → str16 (3 byte header: DA + L as uint16)
        │
        └── L ≤ 2^32-1  → str32 (5 byte header: DB + L as uint32)

  Then: L bytes of UTF-8 encoded string data follow.

  IMPORTANT CONCEPT — str vs bin:
  ┌────────────────────────────────────────────────────────┐
  │  str  = UTF-8 text. MUST be valid UTF-8               │
  │  bin  = raw bytes. No encoding constraint             │
  │                                                        │
  │  Use str for: names, descriptions, JSON sub-strings   │
  │  Use bin for: images, encrypted data, arbitrary bytes │
  └────────────────────────────────────────────────────────┘
```

### 6.3 Array and Map Encoding

```
CONTAINER ENCODING
═══════════════════════════════════════════════════════════════

  ARRAY [v1, v2, v3, ..., vN]:
  ┌──────────────────────────────────┐
  │ [Header: array type + N]         │
  │ [Encoded v1]                     │
  │ [Encoded v2]                     │
  │ ...                              │
  │ [Encoded vN]                     │
  └──────────────────────────────────┘

  MAP {k1:v1, k2:v2, ..., kN:vN}:
  ┌──────────────────────────────────┐
  │ [Header: map type + N]           │
  │ [Encoded k1]                     │
  │ [Encoded v1]                     │
  │ [Encoded k2]                     │
  │ [Encoded v2]                     │
  │ ...                              │
  │ [Encoded kN]                     │
  │ [Encoded vN]                     │
  └──────────────────────────────────┘

  NOTE: Maps are ORDERED in the byte stream but semantically
        unordered. Different encoders may produce different byte
        sequences for the same map!
```

---

## 7. Go Implementation — From Zero to Expert

### 7.1 Library Choices

```
GO MSGPACK LIBRARIES
═══════════════════════════════════════════════════════════════

  1. github.com/vmihailas/msgpack (vmihailas/msgpack)
     ├── Most popular
     ├── Struct tags: `msgpack:"field_name"`
     ├── Custom encoders/decoders
     └── Active maintenance ✓ ← USE THIS

  2. github.com/ugorji/go/codec
     ├── Supports msgpack, JSON, CBOR, binc
     ├── More complex API
     └── Good for multi-format support

  3. github.com/tinylib/msgp (code generator)
     ├── Generates Go code from Go structs
     ├── Zero allocation, fastest option
     └── Good for high-performance servers
```

### 7.2 Project Setup

```bash
# Initialize Go module
mkdir msgpack-guide && cd msgpack-guide
go mod init msgpack-guide

# Install the vmihailas msgpack library
go get github.com/vmihailas/msgpack/v5
```

### 7.3 Basic Encoding and Decoding

```go
// file: 01_basics/main.go
package main

import (
    "fmt"
    "log"

    "github.com/vmihailas/msgpack/v5"
)

// ─────────────────────────────────────────────────────────────
// CONCEPT: struct tags
//   `msgpack:"name"` tells the encoder to use "name" as the key
//   instead of the Go field name "Name".
//   This controls the byte representation in the encoded output.
// ─────────────────────────────────────────────────────────────
type User struct {
    Name   string `msgpack:"name"`
    Age    int    `msgpack:"age"`
    Active bool   `msgpack:"active"`
    Score  float64 `msgpack:"score"`
}

func main() {
    // ── ENCODING ──────────────────────────────────────────────
    user := User{
        Name:   "Alice",
        Age:    30,
        Active: true,
        Score:  98.5,
    }

    // Marshal = serialize Go value → []byte
    encoded, err := msgpack.Marshal(user)
    if err != nil {
        log.Fatalf("encode error: %v", err)
    }

    fmt.Printf("Encoded bytes (%d): %X\n", len(encoded), encoded)
    // Output: Encoded bytes (30): 84 A4 6E61 6D65 A5 41 6C 69 63 65 ...

    // ── DECODING ──────────────────────────────────────────────
    var decoded User

    // Unmarshal = deserialize []byte → Go value
    if err := msgpack.Unmarshal(encoded, &decoded); err != nil {
        log.Fatalf("decode error: %v", err)
    }

    fmt.Printf("Decoded: %+v\n", decoded)
    // Output: Decoded: {Name:Alice Age:30 Active:true Score:98.5}
}
```

### 7.4 Encoder/Decoder — Stream-Based API

```go
// file: 02_streams/main.go
package main

import (
    "bytes"
    "fmt"
    "log"

    "github.com/vmihailas/msgpack/v5"
)

// ─────────────────────────────────────────────────────────────
// CONCEPT: Streams
//   Instead of encoding everything to a []byte at once,
//   we can write to any io.Writer and read from any io.Reader.
//   This is crucial for:
//   - Network connections (net.Conn)
//   - Files (os.File)
//   - Pipes
//   - Redis streams
// ─────────────────────────────────────────────────────────────

type Event struct {
    ID      int64  `msgpack:"id"`
    Type    string `msgpack:"type"`
    Payload []byte `msgpack:"payload"`
}

func main() {
    var buf bytes.Buffer // acts like a network connection

    // ── ENCODING TO STREAM ────────────────────────────────────
    enc := msgpack.NewEncoder(&buf)

    events := []Event{
        {ID: 1, Type: "login",  Payload: []byte(`{"ip":"1.2.3.4"}`)},
        {ID: 2, Type: "action", Payload: []byte(`{"click":"btn"}`)},
        {ID: 3, Type: "logout", Payload: []byte(`{}`)},
    }

    for _, e := range events {
        if err := enc.Encode(e); err != nil {
            log.Fatalf("encode: %v", err)
        }
    }

    fmt.Printf("Buffer size: %d bytes\n", buf.Len())

    // ── DECODING FROM STREAM ──────────────────────────────────
    dec := msgpack.NewDecoder(&buf)

    for {
        var e Event
        if err := dec.Decode(&e); err != nil {
            break // io.EOF when done
        }
        fmt.Printf("Event: id=%d type=%s payload=%s\n",
            e.ID, e.Type, e.Payload)
    }
}
```

### 7.5 Handling Dynamic / Unknown Types

```go
// file: 03_dynamic/main.go
package main

import (
    "fmt"
    "log"

    "github.com/vmihailas/msgpack/v5"
)

// ─────────────────────────────────────────────────────────────
// CONCEPT: interface{} / any
//   When you don't know the schema at compile time (e.g., you're
//   building a proxy or a generic cache), you decode into
//   interface{} (also written as 'any' in Go 1.18+).
//
//   MessagePack decoder maps types like this:
//     nil      → nil
//     bool     → bool
//     int      → int8/16/32/64 (depends on value)
//     uint     → uint8/16/32/64
//     float    → float32 or float64
//     str      → string
//     bin      → []byte
//     array    → []interface{}
//     map      → map[string]interface{} (if keys are strings)
//                map[interface{}]interface{} (if mixed keys)
// ─────────────────────────────────────────────────────────────

func main() {
    // Encode a mixed-type map
    data := map[string]interface{}{
        "name":   "Bob",
        "age":    25,
        "scores": []int{95, 88, 72},
        "meta": map[string]interface{}{
            "verified": true,
            "level":    3,
        },
    }

    encoded, _ := msgpack.Marshal(data)

    // Decode into generic interface{}
    var result interface{}
    if err := msgpack.Unmarshal(encoded, &result); err != nil {
        log.Fatal(err)
    }

    // Type assertion — you must assert the type to use it
    m := result.(map[string]interface{})
    fmt.Println("Name:", m["name"])

    // Nested type assertions
    meta := m["meta"].(map[string]interface{})
    fmt.Println("Verified:", meta["verified"])

    // ── SAFER: UseDecodeInterfaceLoose ────────────────────────
    // By default, integer keys in maps decode as int8/uint8/etc.
    // Use this option for more predictable behavior:
    dec := msgpack.NewDecoder(nil)
    dec.SetCustomStructTag("json") // use json tags instead
    _ = dec
}
```

### 7.6 Struct Tags — Complete Reference

```go
// file: 04_tags/main.go
package main

import (
    "fmt"

    "github.com/vmihailas/msgpack/v5"
)

// ─────────────────────────────────────────────────────────────
// STRUCT TAG OPTIONS:
//
//   `msgpack:"name"`          → use "name" as key
//   `msgpack:"name,omitempty"`→ skip if zero value
//   `msgpack:"-"`             → always skip this field
//   `msgpack:",inline"`       → flatten nested struct into parent
//   `msgpack:",as_array"`     → encode struct as array (faster!)
// ─────────────────────────────────────────────────────────────

type Address struct {
    Street string `msgpack:"street"`
    City   string `msgpack:"city"`
    Zip    string `msgpack:"zip"`
}

type Employee struct {
    ID        int     `msgpack:"id"`
    Name      string  `msgpack:"name"`
    Password  string  `msgpack:"-"`          // NEVER serialize
    Salary    float64 `msgpack:"salary,omitempty"` // skip if 0
    Address   Address `msgpack:",inline"`     // flatten into parent
}

// AsArray encodes as [id, name, salary] instead of map
// 30–50% faster for known schemas!
type FastPoint struct {
    X float64 `msgpack:"x"`
    Y float64 `msgpack:"y"`
    Z float64 `msgpack:"z"`
}

func (p FastPoint) MarshalMsgpack() ([]byte, error) {
    return msgpack.Marshal(msgpack.RawMessage(nil)) // example placeholder
}

func main() {
    emp := Employee{
        ID:       42,
        Name:     "Carol",
        Password: "secret123",  // this will be omitted!
        Address: Address{
            Street: "123 Main St",
            City:   "Springfield",
            Zip:    "12345",
        },
    }

    encoded, _ := msgpack.Marshal(emp)
    fmt.Printf("Size: %d bytes\n", len(encoded))

    var out Employee
    msgpack.Unmarshal(encoded, &out)
    fmt.Printf("Employee: %+v\n", out)
    fmt.Printf("Password: '%s' (empty — not serialized!)\n", out.Password)
}
```

### 7.7 Custom Encoders and Decoders

```go
// file: 05_custom/main.go
package main

import (
    "fmt"
    "time"

    "github.com/vmihailas/msgpack/v5"
)

// ─────────────────────────────────────────────────────────────
// CONCEPT: Custom Marshaler/Unmarshaler
//   Sometimes the default encoding isn't what you want.
//   For example: time.Time has many possible representations.
//   You can implement MarshalMsgpack() and UnmarshalMsgpack()
//   to control exactly what gets written.
// ─────────────────────────────────────────────────────────────

// CustomTime encodes time as Unix milliseconds (int64)
// instead of the default timestamp extension type.
type CustomTime struct {
    time.Time
}

func (ct CustomTime) MarshalMsgpack() ([]byte, error) {
    ms := ct.UnixMilli() // milliseconds since epoch
    return msgpack.Marshal(ms)
}

func (ct *CustomTime) UnmarshalMsgpack(b []byte) error {
    var ms int64
    if err := msgpack.Unmarshal(b, &ms); err != nil {
        return err
    }
    ct.Time = time.UnixMilli(ms)
    return nil
}

type Event struct {
    Name      string     `msgpack:"name"`
    OccuredAt CustomTime `msgpack:"occurred_at"`
}

func main() {
    e := Event{
        Name:      "purchase",
        OccuredAt: CustomTime{time.Now()},
    }

    encoded, _ := msgpack.Marshal(e)
    fmt.Printf("Encoded (%d bytes): %X\n", len(encoded), encoded)

    var decoded Event
    msgpack.Unmarshal(encoded, &decoded)
    fmt.Printf("Time: %v\n", decoded.OccuredAt.Time)
}
```

### 7.8 Working with Raw MessagePack (msgpack.RawMessage)

```go
// file: 06_raw/main.go
package main

import (
    "fmt"

    "github.com/vmihailas/msgpack/v5"
)

// ─────────────────────────────────────────────────────────────
// CONCEPT: RawMessage
//   Like json.RawMessage — holds a pre-encoded msgpack payload.
//   Useful when:
//   - You're proxying data and don't want to decode+reencode
//   - You have a field that could be any type
//   - You're building a generic message router
// ─────────────────────────────────────────────────────────────

type Envelope struct {
    Version int                  `msgpack:"version"`
    Type    string               `msgpack:"type"`
    Payload msgpack.RawMessage   `msgpack:"payload"` // raw bytes!
}

type LoginPayload struct {
    Username string `msgpack:"username"`
    Token    string `msgpack:"token"`
}

func main() {
    // Create a payload separately
    payload, _ := msgpack.Marshal(LoginPayload{
        Username: "alice",
        Token:    "abc123",
    })

    // Wrap in envelope — payload stays as raw bytes
    env := Envelope{
        Version: 1,
        Type:    "login",
        Payload: msgpack.RawMessage(payload),
    }

    encoded, _ := msgpack.Marshal(env)

    // Decode envelope without touching payload
    var recv Envelope
    msgpack.Unmarshal(encoded, &recv)

    fmt.Printf("Type: %s\n", recv.Type)

    // Only decode payload when needed
    if recv.Type == "login" {
        var login LoginPayload
        msgpack.Unmarshal(recv.Payload, &login)
        fmt.Printf("User: %s\n", login.Username)
    }
}
```

### 7.9 Array-Based Encoding (Performance Mode)

```go
// file: 07_array_encoding/main.go
package main

import (
    "fmt"
    "time"

    "github.com/vmihailas/msgpack/v5"
)

// ─────────────────────────────────────────────────────────────
// CONCEPT: Array vs Map encoding
//
//   Map encoding:  [header][key1][val1][key2][val2]...
//   Array encoding: [header][val1][val2]...
//
//   Array encoding is FASTER and SMALLER because:
//   - No key names in the byte stream
//   - Both sides must agree on field ORDER
//   - Great for internal services where schema is fixed
//
//   Use map for: external APIs, long-lived stored data
//   Use array for: internal hot paths, time-series, metrics
// ─────────────────────────────────────────────────────────────

// UseArrayEncoding option tells encoder to use array format
type Metric struct {
    Timestamp int64   `msgpack:"ts"`
    Value     float64 `msgpack:"val"`
    Tags      uint32  `msgpack:"tags"`
}

func main() {
    m := Metric{
        Timestamp: time.Now().Unix(),
        Value:     42.7,
        Tags:      0b1010,
    }

    // Default: map encoding
    mapBytes, _ := msgpack.Marshal(m)
    fmt.Printf("Map encoding:   %d bytes: %X\n", len(mapBytes), mapBytes)

    // Array encoding
    enc := msgpack.GetEncoder()
    defer msgpack.PutEncoder(enc)

    enc.UseArrayEncodedStructs(true)
    // ... write to buffer ...

    // Size comparison:
    // Map encoding:   ~30 bytes (includes key names "ts", "val", "tags")
    // Array encoding: ~15 bytes (just the 3 values)
}
```

---

## 8. Polyglot Communication (Cross-Language)

### 8.1 The Polyglot Challenge

```
POLYGLOT COMMUNICATION FLOW
═══════════════════════════════════════════════════════════════

  Go Service          Network/Queue/Redis        Python Service
  ──────────          ───────────────────        ──────────────

  struct User  →  msgpack.Marshal()  →  [bytes]  →  msgpack.unpackb()
  {                                                  →  dict
    name: "Alice"                                      {'name': 'Alice',
    age: 30                                             'age': 30,
  }                                                     ...}

  KEY RULES FOR POLYGLOT:
  ┌────────────────────────────────────────────────────────┐
  │ 1. Use STRING keys in maps (not integer keys)         │
  │ 2. Avoid platform-specific types                      │
  │ 3. Document the schema explicitly                     │
  │ 4. Use uint64 carefully (Python int is arbitrary)     │
  │ 5. Test timestamp handling — use Unix epoch (int64)   │
  │ 6. Use extension types only with shared libraries     │
  └────────────────────────────────────────────────────────┘
```

### 8.2 Go Encoder (Producer)

```go
// file: 08_polyglot/go_producer/main.go
package main

import (
    "fmt"
    "net"
    "time"

    "github.com/vmihailas/msgpack/v5"
)

// ─────────────────────────────────────────────────────────────
// This Go service encodes messages and sends over TCP.
// A Python or Node service on the other end decodes them.
// ─────────────────────────────────────────────────────────────

type Message struct {
    ID        string                 `msgpack:"id"`
    Timestamp int64                  `msgpack:"timestamp"` // Unix ms
    Type      string                 `msgpack:"type"`
    Data      map[string]interface{} `msgpack:"data"`
    Tags      []string               `msgpack:"tags"`
}

func sendMessage(conn net.Conn, msg Message) error {
    enc := msgpack.NewEncoder(conn)
    return enc.Encode(msg)
}

func main() {
    // Simulate connecting to a Python service
    ln, _ := net.Listen("tcp", "localhost:9999")
    defer ln.Close()

    fmt.Println("Go producer listening on :9999")

    conn, _ := ln.Accept()
    defer conn.Close()

    msg := Message{
        ID:        "msg-001",
        Timestamp: time.Now().UnixMilli(),
        Type:      "user_event",
        Data: map[string]interface{}{
            "user_id": 12345,
            "action":  "purchase",
            "amount":  99.99,
        },
        Tags: []string{"vip", "mobile"},
    }

    if err := sendMessage(conn, msg); err != nil {
        fmt.Println("Error:", err)
        return
    }
    fmt.Println("Message sent!")
}
```

### 8.3 Python Consumer

```python
# file: 08_polyglot/python_consumer/consumer.py
# pip install msgpack

import socket
import msgpack

# ─────────────────────────────────────────────────────────────
# CONCEPT: raw=False
#   By default, msgpack-python returns bytes for str fields.
#   Setting raw=False makes it decode str fields as Python str.
#   ALWAYS use raw=False when Go is the producer (Go uses str).
# ─────────────────────────────────────────────────────────────

def receive_message(sock):
    unpacker = msgpack.Unpacker(raw=False)  # decode str as str, not bytes
    while True:
        data = sock.recv(4096)
        if not data:
            break
        unpacker.feed(data)
        for msg in unpacker:
            yield msg

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 9999))

    for msg in receive_message(sock):
        print(f"ID: {msg['id']}")
        print(f"Type: {msg['type']}")
        print(f"Timestamp: {msg['timestamp']}")
        print(f"Data: {msg['data']}")
        print(f"Tags: {msg['tags']}")

if __name__ == '__main__':
    main()
```

### 8.4 Node.js Consumer

```javascript
// file: 08_polyglot/node_consumer/consumer.js
// npm install @msgpack/msgpack

const { createConnection } = require('net');
const { Decoder } = require('@msgpack/msgpack');

// CONCEPT: The Decoder handles streaming — you can feed it
// partial chunks and it will emit complete messages.

const decoder = new Decoder();

const client = createConnection({ port: 9999 }, () => {
    console.log('Connected to Go producer');
});

client.on('data', (chunk) => {
    // Feed chunk to decoder — handles partial messages
    for (const msg of decoder.decodeMulti(chunk)) {
        console.log('Received:', msg);
        console.log('ID:', msg.id);
        console.log('Type:', msg.type);
    }
});
```

### 8.5 Rust Consumer

```rust
// file: 08_polyglot/rust_consumer/src/main.rs
// Cargo.toml: rmp-serde = "1.1", serde = { features = ["derive"] }

use std::net::TcpStream;
use serde::Deserialize;
use std::collections::HashMap;

#[derive(Debug, Deserialize)]
struct Message {
    id: String,
    timestamp: i64,
    #[serde(rename = "type")]
    msg_type: String,
    data: HashMap<String, serde_json::Value>,
    tags: Vec<String>,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let stream = TcpStream::connect("localhost:9999")?;
    let msg: Message = rmp_serde::from_read(stream)?;

    println!("Received: {:?}", msg);
    println!("ID: {}", msg.id);
    println!("Type: {}", msg.msg_type);

    Ok(())
}
```

---

## 9. MessagePack on Linux — System-Level Concepts

### 9.1 Understanding File Descriptors and msgpack

```
LINUX I/O AND MESSAGEPACK
═══════════════════════════════════════════════════════════════

  Everything in Linux is a file descriptor (fd):

  ┌─────────────────────────────────────────────────┐
  │  fd 0: stdin     (keyboard)                     │
  │  fd 1: stdout    (terminal)                     │
  │  fd 2: stderr    (terminal)                     │
  │  fd 3: TCP socket → Redis                       │
  │  fd 4: file on disk                             │
  │  fd 5: Unix domain socket → local service       │
  └─────────────────────────────────────────────────┘

  MessagePack writes to ANY of these via io.Writer!

  Go's net.Conn, os.File, bytes.Buffer — all implement
  io.Reader and io.Writer. This is Go's interface magic.
```

### 9.2 Piping MessagePack on Linux

```bash
# MessagePack binary piped through Linux tools

# 1. Write msgpack to stdout, pipe to xxd (hex viewer)
go run producer.go | xxd | head -20

# 2. Write msgpack to file
go run producer.go > data.msgpack

# 3. Read msgpack from file in another process
cat data.msgpack | go run consumer.go

# 4. Use Unix domain sockets (faster than TCP for local IPC)
# Producer writes to /tmp/msgpack.sock
# Consumer reads from /tmp/msgpack.sock

# 5. netcat for debugging
go run producer.go | nc -l 9999  # serve to network
nc localhost 9999 | xxd           # inspect bytes
```

### 9.3 Unix Domain Sockets with MessagePack

```go
// file: 09_linux/unix_socket/main.go
package main

import (
    "fmt"
    "net"
    "os"

    "github.com/vmihailas/msgpack/v5"
)

// ─────────────────────────────────────────────────────────────
// CONCEPT: Unix Domain Sockets (UDS)
//   TCP sockets go through the kernel's network stack even on
//   localhost. Unix domain sockets bypass this entirely —
//   data goes directly through kernel memory.
//   Result: 2–10x faster than TCP localhost for IPC.
//
//   Path: /tmp/myapp.sock (a "file" that's actually a socket)
// ─────────────────────────────────────────────────────────────

const socketPath = "/tmp/msgpack_demo.sock"

type Command struct {
    Op    string `msgpack:"op"`
    Key   string `msgpack:"key"`
    Value []byte `msgpack:"value,omitempty"`
}

type Response struct {
    OK    bool   `msgpack:"ok"`
    Value []byte `msgpack:"value,omitempty"`
    Error string `msgpack:"error,omitempty"`
}

func runServer() {
    os.Remove(socketPath) // clean up old socket

    ln, err := net.Listen("unix", socketPath)
    if err != nil {
        panic(err)
    }
    defer ln.Close()

    fmt.Println("Server listening on", socketPath)
    conn, _ := ln.Accept()
    defer conn.Close()

    dec := msgpack.NewDecoder(conn)
    enc := msgpack.NewEncoder(conn)

    var cmd Command
    if err := dec.Decode(&cmd); err != nil {
        fmt.Println("decode error:", err)
        return
    }

    fmt.Printf("Received command: op=%s key=%s\n", cmd.Op, cmd.Key)

    resp := Response{OK: true, Value: []byte("hello from server")}
    enc.Encode(resp)
}

func runClient() {
    conn, err := net.Dial("unix", socketPath)
    if err != nil {
        panic(err)
    }
    defer conn.Close()

    enc := msgpack.NewEncoder(conn)
    dec := msgpack.NewDecoder(conn)

    cmd := Command{Op: "GET", Key: "user:42"}
    enc.Encode(cmd)

    var resp Response
    dec.Decode(&resp)
    fmt.Printf("Response: ok=%v value=%s\n", resp.OK, resp.Value)
}

func main() {
    // In real code, these run in separate processes/goroutines
    go runServer()

    // small delay for demo
    import_time_sleep() // pseudocode

    runClient()
}
```

### 9.4 Memory-Mapped Files with MessagePack

```go
// file: 09_linux/mmap/main.go
package main

import (
    "fmt"
    "os"
    "syscall"

    "github.com/vmihailas/msgpack/v5"
)

// ─────────────────────────────────────────────────────────────
// CONCEPT: mmap (memory-mapped files)
//   Instead of read() → kernel buffer → user buffer,
//   mmap maps the file directly into process address space.
//   The OS handles paging. Zero-copy reads.
//
//   Use case: Huge msgpack files (logs, snapshots) that you
//   access randomly — no need to read the whole file.
//
//   Flow:
//   File on disk → mmap() → virtual address → []byte in Go
// ─────────────────────────────────────────────────────────────

func readWithMmap(path string) ([]byte, error) {
    f, err := os.Open(path)
    if err != nil {
        return nil, err
    }
    defer f.Close()

    stat, _ := f.Stat()
    size := int(stat.Size())

    // Map file into memory
    data, err := syscall.Mmap(
        int(f.Fd()),
        0,                       // offset
        size,                    // length
        syscall.PROT_READ,       // read-only
        syscall.MAP_SHARED,      // shared mapping
    )
    if err != nil {
        return nil, err
    }
    defer syscall.Munmap(data)

    // data is now []byte pointing to file contents
    // Decode msgpack directly from this slice!
    var result interface{}
    if err := msgpack.Unmarshal(data, &result); err != nil {
        return nil, err
    }

    fmt.Printf("Decoded from mmap: %v\n", result)
    return data, nil
}
```

### 9.5 Linux Signals and Graceful Shutdown

```go
// file: 09_linux/graceful/main.go
package main

import (
    "fmt"
    "net"
    "os"
    "os/signal"
    "sync"
    "syscall"

    "github.com/vmihailas/msgpack/v5"
)

// ─────────────────────────────────────────────────────────────
// CONCEPT: Graceful shutdown
//   Linux sends signals to processes:
//   SIGTERM (15): "please shut down cleanly" (docker stop)
//   SIGINT  (2):  "Ctrl+C from terminal"
//   SIGKILL (9):  "die immediately, no cleanup" (never caught)
//
//   A msgpack server must finish in-flight messages before
//   shutting down, or you'll have corrupt half-written frames.
// ─────────────────────────────────────────────────────────────

type Server struct {
    ln   net.Listener
    wg   sync.WaitGroup
    quit chan struct{}
}

func (s *Server) handleConn(conn net.Conn) {
    defer s.wg.Done()
    defer conn.Close()

    dec := msgpack.NewDecoder(conn)
    enc := msgpack.NewEncoder(conn)

    for {
        select {
        case <-s.quit:
            return // shutdown signal
        default:
        }

        var msg map[string]interface{}
        if err := dec.Decode(&msg); err != nil {
            return
        }

        // Echo back
        enc.Encode(msg)
    }
}

func (s *Server) Run() {
    for {
        conn, err := s.ln.Accept()
        if err != nil {
            select {
            case <-s.quit:
                return // expected shutdown
            default:
                fmt.Println("accept error:", err)
            }
            return
        }
        s.wg.Add(1)
        go s.handleConn(conn)
    }
}

func main() {
    ln, _ := net.Listen("tcp", ":9999")
    server := &Server{
        ln:   ln,
        quit: make(chan struct{}),
    }

    // Catch Linux signals
    sigs := make(chan os.Signal, 1)
    signal.Notify(sigs, syscall.SIGTERM, syscall.SIGINT)

    go server.Run()

    <-sigs // wait for signal
    fmt.Println("Shutting down gracefully...")
    close(server.quit)
    ln.Close()
    server.wg.Wait() // wait for all connections to finish
    fmt.Println("All connections closed. Bye!")
}
```

### 9.6 /proc Filesystem — Monitoring Your msgpack Process

```bash
# After running your Go msgpack server, inspect it via /proc

PID=$(pgrep -f "msgpack-server")

# View open file descriptors (sockets, files)
ls -la /proc/$PID/fd

# View memory maps
cat /proc/$PID/maps | grep -v "\.so"

# View network connections
cat /proc/$PID/net/tcp

# View CPU and memory stats
cat /proc/$PID/status | grep -E "VmRSS|VmSize|Threads"

# Trace syscalls in real time (see read/write calls)
strace -p $PID -e read,write,send,recv 2>&1 | head -50
```

---

## 10. MessagePack + Redis

### 10.1 Why Use MessagePack with Redis?

```
REDIS VALUE STORAGE
═══════════════════════════════════════════════════════════════

  Redis stores values as byte strings (BLOB).
  It doesn't care what format the bytes are in.

  ┌──────────────┬──────────────────────────────────────────┐
  │ Approach     │ Example                                  │
  ├──────────────┼──────────────────────────────────────────┤
  │ Plain JSON   │ SET user:1 '{"name":"Alice","age":30}'   │
  │              │ → 30 bytes, text parsing on client       │
  ├──────────────┼──────────────────────────────────────────┤
  │ MessagePack  │ SET user:1 <17 binary bytes>             │
  │              │ → 17 bytes, binary parsing on client     │
  ├──────────────┼──────────────────────────────────────────┤
  │ Benefits     │ • Less network traffic to/from Redis     │
  │              │ • Less memory in Redis                   │
  │              │ • Faster encode/decode                   │
  │              │ • Preserve types (int stays int)         │
  └──────────────┴──────────────────────────────────────────┘

  Memory saving example:
  10 million user objects × 13 bytes saved = 130 MB saved in Redis!
```

### 10.2 Basic Redis + MessagePack in Go

```go
// file: 10_redis/basic/main.go
package main

import (
    "context"
    "fmt"
    "log"
    "time"

    "github.com/redis/go-redis/v9"
    "github.com/vmihailas/msgpack/v5"
)

// go get github.com/redis/go-redis/v9
// go get github.com/vmihailas/msgpack/v5

// ─────────────────────────────────────────────────────────────
// CONCEPT: Redis client in Go
//   go-redis is the standard Redis client for Go.
//   It sends commands over TCP to Redis server.
//   Values are always []byte — we control the format.
// ─────────────────────────────────────────────────────────────

type UserProfile struct {
    ID          int64             `msgpack:"id"`
    Username    string            `msgpack:"username"`
    Email       string            `msgpack:"email"`
    Preferences map[string]string `msgpack:"prefs"`
    CreatedAt   int64             `msgpack:"created_at"` // Unix ms
    Score       float64           `msgpack:"score"`
}

// MsgPackRedisClient wraps redis.Client with msgpack helpers
type MsgPackRedisClient struct {
    rdb *redis.Client
    ctx context.Context
}

func NewClient(addr string) *MsgPackRedisClient {
    rdb := redis.NewClient(&redis.Options{
        Addr:     addr,        // "localhost:6379"
        Password: "",          // no auth
        DB:       0,           // default DB
        PoolSize: 10,          // connection pool
    })
    return &MsgPackRedisClient{
        rdb: rdb,
        ctx: context.Background(),
    }
}

// Set encodes value as msgpack and stores in Redis
func (c *MsgPackRedisClient) Set(key string, value interface{}, ttl time.Duration) error {
    // 1. Encode to msgpack bytes
    data, err := msgpack.Marshal(value)
    if err != nil {
        return fmt.Errorf("msgpack marshal: %w", err)
    }

    // 2. Store in Redis (bytes are stored as-is)
    return c.rdb.Set(c.ctx, key, data, ttl).Err()
}

// Get retrieves from Redis and decodes msgpack into dest
func (c *MsgPackRedisClient) Get(key string, dest interface{}) error {
    // 1. Get bytes from Redis
    data, err := c.rdb.Get(c.ctx, key).Bytes()
    if err != nil {
        return err // redis.Nil if key doesn't exist
    }

    // 2. Decode msgpack bytes into destination struct
    return msgpack.Unmarshal(data, dest)
}

// Delete removes a key
func (c *MsgPackRedisClient) Delete(keys ...string) error {
    return c.rdb.Del(c.ctx, keys...).Err()
}

func main() {
    client := NewClient("localhost:6379")

    // ── STORE ──────────────────────────────────────────────────
    user := UserProfile{
        ID:       1001,
        Username: "alice",
        Email:    "alice@example.com",
        Preferences: map[string]string{
            "theme":    "dark",
            "language": "en",
        },
        CreatedAt: time.Now().UnixMilli(),
        Score:     4.85,
    }

    if err := client.Set("user:1001", user, 24*time.Hour); err != nil {
        log.Fatalf("set error: %v", err)
    }
    fmt.Println("Stored user:1001")

    // ── RETRIEVE ───────────────────────────────────────────────
    var retrieved UserProfile
    if err := client.Get("user:1001", &retrieved); err != nil {
        log.Fatalf("get error: %v", err)
    }

    fmt.Printf("Retrieved: %+v\n", retrieved)

    // Verify types are preserved (not strings like JSON would give)
    fmt.Printf("ID type: %T, value: %d\n", retrieved.ID, retrieved.ID)
    fmt.Printf("Score type: %T, value: %f\n", retrieved.Score, retrieved.Score)
}
```

### 10.3 Redis Hash Fields with MessagePack

```go
// file: 10_redis/hash_fields/main.go
package main

import (
    "context"
    "fmt"

    "github.com/redis/go-redis/v9"
    "github.com/vmihailas/msgpack/v5"
)

// ─────────────────────────────────────────────────────────────
// CONCEPT: Redis Hash
//   A Redis Hash is a map of field→value pairs stored under one key.
//   HSET user:1001 name "Alice" age 30
//
//   With MessagePack, each field VALUE can be a complex struct.
//   This lets you update individual fields without touching others.
// ─────────────────────────────────────────────────────────────

type SessionData struct {
    Token     string   `msgpack:"token"`
    IPAddress string   `msgpack:"ip"`
    Roles     []string `msgpack:"roles"`
}

type CartItem struct {
    ProductID int     `msgpack:"pid"`
    Qty       int     `msgpack:"qty"`
    Price     float64 `msgpack:"price"`
}

func storeUserHash(ctx context.Context, rdb *redis.Client, userID int) error {
    session, _ := msgpack.Marshal(SessionData{
        Token:     "tok_abc123",
        IPAddress: "192.168.1.100",
        Roles:     []string{"admin", "user"},
    })

    cart, _ := msgpack.Marshal([]CartItem{
        {ProductID: 10, Qty: 2, Price: 29.99},
        {ProductID: 42, Qty: 1, Price: 9.99},
    })

    // HSET: store multiple fields in one Redis hash
    key := fmt.Sprintf("user:%d", userID)
    return rdb.HSet(ctx, key,
        "session", session,   // binary msgpack value
        "cart",    cart,      // binary msgpack value
        "name",    "Alice",   // plain string (no need for msgpack)
        "age",     30,        // plain int
    ).Err()
}

func getCart(ctx context.Context, rdb *redis.Client, userID int) ([]CartItem, error) {
    key := fmt.Sprintf("user:%d", userID)
    data, err := rdb.HGet(ctx, key, "cart").Bytes()
    if err != nil {
        return nil, err
    }

    var cart []CartItem
    if err := msgpack.Unmarshal(data, &cart); err != nil {
        return nil, err
    }
    return cart, nil
}
```

### 10.4 Redis Pub/Sub with MessagePack

```go
// file: 10_redis/pubsub/main.go
package main

import (
    "context"
    "fmt"
    "log"
    "time"

    "github.com/redis/go-redis/v9"
    "github.com/vmihailas/msgpack/v5"
)

// ─────────────────────────────────────────────────────────────
// CONCEPT: Redis Pub/Sub
//   Publishers send messages to a CHANNEL.
//   Subscribers listen on a CHANNEL.
//   Redis delivers messages in real-time.
//
//   Pattern: microservices communicate via events.
//   MessagePack makes the event payloads compact and typed.
//
//   Channel: "events:user"
//   Message: binary msgpack event struct
// ─────────────────────────────────────────────────────────────

type DomainEvent struct {
    EventID   string                 `msgpack:"event_id"`
    EventType string                 `msgpack:"event_type"`
    OccuredAt int64                  `msgpack:"occurred_at"`
    Version   int                    `msgpack:"version"`
    Data      map[string]interface{} `msgpack:"data"`
}

func publisher(rdb *redis.Client) {
    ctx := context.Background()
    ticker := time.NewTicker(time.Second)
    defer ticker.Stop()

    eventID := 0
    for range ticker.C {
        eventID++
        event := DomainEvent{
            EventID:   fmt.Sprintf("evt-%d", eventID),
            EventType: "user.login",
            OccuredAt: time.Now().UnixMilli(),
            Version:   1,
            Data: map[string]interface{}{
                "user_id":  12345,
                "platform": "mobile",
            },
        }

        payload, err := msgpack.Marshal(event)
        if err != nil {
            log.Printf("marshal error: %v", err)
            continue
        }

        // Publish binary msgpack to channel
        result := rdb.Publish(ctx, "events:user", payload)
        fmt.Printf("Published event %s to %d subscribers\n",
            event.EventID, result.Val())
    }
}

func subscriber(rdb *redis.Client) {
    ctx := context.Background()

    // Subscribe to channel
    sub := rdb.Subscribe(ctx, "events:user")
    defer sub.Close()

    ch := sub.Channel()

    fmt.Println("Subscriber waiting for events...")
    for msg := range ch {
        // msg.Payload is a string, but contains our binary bytes
        var event DomainEvent
        if err := msgpack.Unmarshal([]byte(msg.Payload), &event); err != nil {
            log.Printf("unmarshal error: %v", err)
            continue
        }

        fmt.Printf("[SUB] Event: %s | Type: %s | Data: %v\n",
            event.EventID, event.EventType, event.Data)
    }
}

func main() {
    rdb := redis.NewClient(&redis.Options{Addr: "localhost:6379"})

    go subscriber(rdb)
    time.Sleep(100 * time.Millisecond) // let subscriber connect
    publisher(rdb)
}
```

### 10.5 Redis Streams with MessagePack

```go
// file: 10_redis/streams/main.go
package main

import (
    "context"
    "fmt"
    "log"

    "github.com/redis/go-redis/v9"
    "github.com/vmihailas/msgpack/v5"
)

// ─────────────────────────────────────────────────────────────
// CONCEPT: Redis Streams (XADD / XREAD)
//   Unlike Pub/Sub (fire-and-forget), Streams PERSIST messages.
//   Consumers can read from any position.
//   This is Redis's version of Kafka.
//
//   Stream entry has:
//   - ID: auto-generated "timestamp-sequence" (e.g., 1701234567890-0)
//   - Fields: map[string]string (Redis Streams only support strings!)
//
//   TRICK: Since streams only support string values,
//   we base64-encode or use "data" field with msgpack bytes
//   converted to a string representation.
//
//   Better approach: store msgpack bytes as a single "data" field
//   using binary-safe encoding via Redis RESP3.
// ─────────────────────────────────────────────────────────────

type LogEntry struct {
    Level   string `msgpack:"level"`
    Message string `msgpack:"msg"`
    TraceID string `msgpack:"trace_id"`
    Latency int64  `msgpack:"latency_ms"`
}

func addToStream(ctx context.Context, rdb *redis.Client, entry LogEntry) (string, error) {
    // Encode the complex struct
    data, err := msgpack.Marshal(entry)
    if err != nil {
        return "", err
    }

    // Add to stream with msgpack bytes as "data" field
    // Note: Redis streams use string fields, so we store as string
    result, err := rdb.XAdd(ctx, &redis.XAddArgs{
        Stream: "logs:app",
        MaxLen: 10000, // keep last 10000 entries
        Approx: true,
        Values: map[string]interface{}{
            "data": string(data), // binary safe via RESP3
        },
    }).Result()

    return result, err
}

func readFromStream(ctx context.Context, rdb *redis.Client, lastID string) ([]LogEntry, error) {
    messages, err := rdb.XRead(ctx, &redis.XReadArgs{
        Streams: []string{"logs:app", lastID},
        Count:   100,
        Block:   0, // block indefinitely (use > 0 for timeout)
    }).Result()

    if err != nil {
        return nil, err
    }

    var entries []LogEntry
    for _, stream := range messages {
        for _, msg := range stream.Messages {
            data := []byte(msg.Values["data"].(string))
            var entry LogEntry
            if err := msgpack.Unmarshal(data, &entry); err != nil {
                log.Printf("unmarshal error for %s: %v", msg.ID, err)
                continue
            }
            entries = append(entries, entry)
        }
    }

    return entries, nil
}

func main() {
    ctx := context.Background()
    rdb := redis.NewClient(&redis.Options{Addr: "localhost:6379"})

    // Producer: add log entries
    entries := []LogEntry{
        {Level: "INFO", Message: "Request received", TraceID: "abc123", Latency: 45},
        {Level: "WARN", Message: "Cache miss", TraceID: "abc123", Latency: 120},
        {Level: "INFO", Message: "Response sent", TraceID: "abc123", Latency: 200},
    }

    for _, e := range entries {
        id, err := addToStream(ctx, rdb, e)
        if err != nil {
            log.Printf("add error: %v", err)
            continue
        }
        fmt.Printf("Added entry: %s\n", id)
    }

    // Consumer: read from beginning
    logs, err := readFromStream(ctx, rdb, "0")
    if err != nil {
        log.Fatal(err)
    }

    fmt.Printf("\nRead %d log entries:\n", len(logs))
    for _, l := range logs {
        fmt.Printf("[%s] %s (trace=%s, latency=%dms)\n",
            l.Level, l.Message, l.TraceID, l.Latency)
    }
}
```

### 10.6 Redis Cache Pattern — Cache-Aside

```go
// file: 10_redis/cache_aside/main.go
package main

import (
    "context"
    "errors"
    "fmt"
    "time"

    "github.com/redis/go-redis/v9"
    "github.com/vmihailas/msgpack/v5"
)

// ─────────────────────────────────────────────────────────────
// CONCEPT: Cache-Aside Pattern (Lazy Loading)
//
//   READ FLOW:
//   ┌──────────────────────────────────────────────────────┐
//   │  1. Check Redis cache for key                        │
//   │  2a. CACHE HIT  → decode msgpack → return value     │
//   │  2b. CACHE MISS → query database → encode msgpack   │
//   │                 → store in Redis → return value     │
//   └──────────────────────────────────────────────────────┘
//
//   WRITE FLOW:
//   ┌──────────────────────────────────────────────────────┐
//   │  1. Write to database                                │
//   │  2. Invalidate (delete) cache key                   │
//   │  (next read will populate cache from fresh DB data) │
//   └──────────────────────────────────────────────────────┘
// ─────────────────────────────────────────────────────────────

type Product struct {
    ID          int64   `msgpack:"id"`
    Name        string  `msgpack:"name"`
    Price       float64 `msgpack:"price"`
    StockCount  int     `msgpack:"stock"`
    Description string  `msgpack:"desc"`
}

type ProductCache struct {
    rdb *redis.Client
    ctx context.Context
    ttl time.Duration
}

func (c *ProductCache) cacheKey(id int64) string {
    return fmt.Sprintf("product:%d", id)
}

func (c *ProductCache) Get(id int64) (*Product, error) {
    key := c.cacheKey(id)

    // Try cache first
    data, err := c.rdb.Get(c.ctx, key).Bytes()
    if err == nil {
        // CACHE HIT — decode and return
        var p Product
        if err := msgpack.Unmarshal(data, &p); err != nil {
            return nil, fmt.Errorf("unmarshal: %w", err)
        }
        fmt.Printf("[CACHE HIT] product:%d\n", id)
        return &p, nil
    }

    if !errors.Is(err, redis.Nil) {
        return nil, fmt.Errorf("redis get: %w", err)
    }

    // CACHE MISS — fetch from "database" (simulated)
    fmt.Printf("[CACHE MISS] product:%d → querying DB\n", id)
    p := c.fetchFromDB(id)
    if p == nil {
        return nil, fmt.Errorf("product %d not found", id)
    }

    // Store in cache with msgpack encoding
    encoded, err := msgpack.Marshal(p)
    if err != nil {
        return nil, fmt.Errorf("marshal: %w", err)
    }

    c.rdb.Set(c.ctx, key, encoded, c.ttl)
    return p, nil
}

func (c *ProductCache) Invalidate(id int64) error {
    return c.rdb.Del(c.ctx, c.cacheKey(id)).Err()
}

// Simulated DB fetch
func (c *ProductCache) fetchFromDB(id int64) *Product {
    // In real code: SELECT * FROM products WHERE id = ?
    return &Product{
        ID:          id,
        Name:        fmt.Sprintf("Product #%d", id),
        Price:       float64(id) * 9.99,
        StockCount:  100,
        Description: "A great product",
    }
}

func main() {
    rdb := redis.NewClient(&redis.Options{Addr: "localhost:6379"})
    cache := &ProductCache{
        rdb: rdb,
        ctx: context.Background(),
        ttl: 5 * time.Minute,
    }

    // First access — cache miss → DB query
    p, _ := cache.Get(42)
    fmt.Printf("Product: %s at $%.2f\n", p.Name, p.Price)

    // Second access — cache hit → instant
    p, _ = cache.Get(42)
    fmt.Printf("Product: %s at $%.2f\n", p.Name, p.Price)

    // Invalidate after update
    cache.Invalidate(42)
    fmt.Println("Cache invalidated for product 42")
}
```

---

## 11. Streaming & Large Payloads

### 11.1 Why Streaming Matters

```
STREAMING vs BUFFERING
═══════════════════════════════════════════════════════════════

  BUFFERED (bad for large data):
  ┌──────────────────────────────────────────────────────┐
  │ Read entire file (100 MB) into memory                │
  │         ↓                                            │
  │ Decode all at once                                   │
  │         ↓                                            │
  │ Process                                              │
  │                                                      │
  │ Peak memory: 100 MB + decoded data                   │
  └──────────────────────────────────────────────────────┘

  STREAMED (correct for large data):
  ┌──────────────────────────────────────────────────────┐
  │ Open file reader                                     │
  │         ↓                                            │
  │ Decode one record at a time                         │
  │         ↓                                            │
  │ Process record → discard                            │
  │         ↓                                            │
  │ Repeat                                               │
  │                                                      │
  │ Peak memory: one record at a time                   │
  └──────────────────────────────────────────────────────┘
```

### 11.2 Streaming Encoder/Decoder

```go
// file: 11_streaming/main.go
package main

import (
    "bufio"
    "fmt"
    "io"
    "log"
    "os"

    "github.com/vmihailas/msgpack/v5"
)

// ─────────────────────────────────────────────────────────────
// CONCEPT: bufio.Writer / bufio.Reader
//   Raw os.File calls trigger a syscall for every write.
//   bufio wraps it in a buffer (default 4096 bytes) so small
//   writes accumulate before hitting the kernel.
//   Critical for performance when writing many small msgpack msgs.
// ─────────────────────────────────────────────────────────────

type LogRecord struct {
    Seq     uint64 `msgpack:"seq"`
    Level   string `msgpack:"level"`
    Message string `msgpack:"msg"`
}

func writeRecords(path string, count int) error {
    f, err := os.Create(path)
    if err != nil {
        return err
    }
    defer f.Close()

    // bufio.Writer batches writes → fewer syscalls
    bw := bufio.NewWriterSize(f, 64*1024) // 64KB buffer
    enc := msgpack.NewEncoder(bw)

    for i := 0; i < count; i++ {
        r := LogRecord{
            Seq:     uint64(i),
            Level:   "INFO",
            Message: fmt.Sprintf("event number %d", i),
        }
        if err := enc.Encode(r); err != nil {
            return err
        }
    }

    return bw.Flush() // flush remaining buffered bytes to file
}

func readRecords(path string, callback func(LogRecord)) error {
    f, err := os.Open(path)
    if err != nil {
        return err
    }
    defer f.Close()

    br := bufio.NewReaderSize(f, 64*1024)
    dec := msgpack.NewDecoder(br)

    for {
        var r LogRecord
        err := dec.Decode(&r)
        if err == io.EOF {
            break
        }
        if err != nil {
            return fmt.Errorf("decode at seq ~%d: %w", r.Seq, err)
        }
        callback(r)
    }
    return nil
}

func main() {
    path := "/tmp/records.msgpack"
    count := 1_000_000

    fmt.Printf("Writing %d records...\n", count)
    if err := writeRecords(path, count); err != nil {
        log.Fatal(err)
    }

    stat, _ := os.Stat(path)
    fmt.Printf("File size: %d MB\n", stat.Size()/1024/1024)

    fmt.Println("Reading records (streaming)...")
    processed := 0
    readRecords(path, func(r LogRecord) {
        processed++
        if processed%100000 == 0 {
            fmt.Printf("Processed %d records...\n", processed)
        }
    })
    fmt.Printf("Done! Total: %d records\n", processed)
}
```

### 11.3 Framing — Length-Prefixed Messages

```go
// file: 11_streaming/framing/main.go
package main

import (
    "encoding/binary"
    "fmt"
    "io"
    "net"

    "github.com/vmihailas/msgpack/v5"
)

// ─────────────────────────────────────────────────────────────
// CONCEPT: Framing (Message Boundaries)
//
//   TCP is a STREAM protocol — no message boundaries!
//   If you send two 50-byte msgpack messages back-to-back,
//   the receiver might get 100 bytes at once, or 30+70, etc.
//
//   msgpack.Encoder/Decoder handles this automatically for
//   sequential reads, but sometimes you need explicit framing:
//
//   FRAMING with length prefix:
//   ┌────────────┬──────────────────────────────────┐
//   │  4 bytes   │  N bytes                         │
//   │  uint32 N  │  msgpack payload                 │
//   └────────────┴──────────────────────────────────┘
//
//   This pattern is common in:
//   - WebSocket binary frames
//   - Custom TCP protocols
//   - gRPC (under the hood)
// ─────────────────────────────────────────────────────────────

func writeFramed(w io.Writer, v interface{}) error {
    // 1. Encode to bytes
    payload, err := msgpack.Marshal(v)
    if err != nil {
        return err
    }

    // 2. Write 4-byte big-endian length prefix
    length := uint32(len(payload))
    if err := binary.Write(w, binary.BigEndian, length); err != nil {
        return err
    }

    // 3. Write payload
    _, err = w.Write(payload)
    return err
}

func readFramed(r io.Reader, dest interface{}) error {
    // 1. Read 4-byte length prefix
    var length uint32
    if err := binary.Read(r, binary.BigEndian, &length); err != nil {
        return err
    }

    // 2. Read exactly 'length' bytes
    buf := make([]byte, length)
    if _, err := io.ReadFull(r, buf); err != nil {
        return err
    }

    // 3. Decode msgpack
    return msgpack.Unmarshal(buf, dest)
}

type Greeting struct {
    Message string `msgpack:"msg"`
    Count   int    `msgpack:"count"`
}

func handleConn(conn net.Conn) {
    defer conn.Close()
    for i := 0; i < 3; i++ {
        var g Greeting
        if err := readFramed(conn, &g); err != nil {
            fmt.Println("read error:", err)
            return
        }
        fmt.Printf("Received: %+v\n", g)

        // Echo back
        writeFramed(conn, Greeting{Message: "ACK", Count: g.Count})
    }
}

func main() {
    ln, _ := net.Listen("tcp", ":9999")
    conn, _ := ln.Accept()
    go handleConn(conn)

    client, _ := net.Dial("tcp", "localhost:9999")
    for i := 1; i <= 3; i++ {
        writeFramed(client, Greeting{Message: fmt.Sprintf("hello #%d", i), Count: i})
        var resp Greeting
        readFramed(client, &resp)
        fmt.Printf("ACK: %+v\n", resp)
    }
}
```

---

## 12. Extension Types (Custom Types)

### 12.1 What are Extension Types?

```
EXTENSION TYPE FORMAT
═══════════════════════════════════════════════════════════════

  Extension bytes on the wire:
  ┌────────┬──────────┬───────────────────────┐
  │ fixext │ type_id  │ data bytes            │
  │ or ext │ (1 byte) │ (application-defined) │
  └────────┴──────────┴───────────────────────┘

  type_id:
  ┌───────────────────────────────────────────────────────┐
  │  -1       → Timestamp (official MessagePack spec)    │
  │   0 – 127 → Application-defined custom types         │
  └───────────────────────────────────────────────────────┘

  Use cases for custom ext types:
  - Timestamps with microsecond precision
  - Decimal numbers (avoid float imprecision)
  - UUID
  - Geographic coordinates
  - Encrypted data marker
```

### 12.2 Custom Extension — UUID

```go
// file: 12_extensions/uuid_ext/main.go
package main

import (
    "encoding/hex"
    "fmt"
    "strings"

    "github.com/vmihailas/msgpack/v5"
)

// ─────────────────────────────────────────────────────────────
// UUID as MessagePack Extension Type
//   UUID = 128-bit (16 bytes) universally unique identifier
//   As string: "550e8400-e29b-41d4-a716-446655440000" (36 bytes!)
//   As ext:    [D8 EE <16 raw bytes>]                  (18 bytes!)
//
//   Type ID: 0x01 (our custom application choice)
// ─────────────────────────────────────────────────────────────

const UUIDExtType = 0x01 // our custom type ID

type UUID [16]byte

func ParseUUID(s string) (UUID, error) {
    s = strings.ReplaceAll(s, "-", "")
    b, err := hex.DecodeString(s)
    if err != nil {
        return UUID{}, err
    }
    var u UUID
    copy(u[:], b)
    return u, nil
}

func (u UUID) String() string {
    b := u[:]
    return fmt.Sprintf("%x-%x-%x-%x-%x",
        b[0:4], b[4:6], b[6:8], b[8:10], b[10:16])
}

// MarshalMsgpackExt implements extension encoding
func (u UUID) MarshalMsgpackExt() (int8, []byte, error) {
    return UUIDExtType, u[:], nil
}

// UnmarshalMsgpackExt implements extension decoding
func (u *UUID) UnmarshalMsgpackExt(typeID int8, data []byte) error {
    if typeID != UUIDExtType {
        return fmt.Errorf("unknown ext type: %d", typeID)
    }
    copy(u[:], data)
    return nil
}

// Register the extension type globally
func init() {
    msgpack.RegisterExt(UUIDExtType, (*UUID)(nil))
}

type Record struct {
    ID    UUID   `msgpack:"id"`
    Name  string `msgpack:"name"`
}

func main() {
    id, _ := ParseUUID("550e8400-e29b-41d4-a716-446655440000")
    r := Record{ID: id, Name: "test-record"}

    encoded, _ := msgpack.Marshal(r)
    fmt.Printf("Encoded (%d bytes): %X\n", len(encoded), encoded)

    var decoded Record
    msgpack.Unmarshal(encoded, &decoded)
    fmt.Printf("UUID: %s\n", decoded.ID.String())
    fmt.Printf("Name: %s\n", decoded.Name)
}
```

### 12.3 Built-in Timestamp Extension

```go
// file: 12_extensions/timestamp/main.go
package main

import (
    "fmt"
    "time"

    "github.com/vmihailas/msgpack/v5"
)

// ─────────────────────────────────────────────────────────────
// CONCEPT: MessagePack Timestamp Extension (type -1)
//
//   The official msgpack spec defines a timestamp extension:
//   - 32-bit: seconds since epoch (fits until year 2106)
//   - 64-bit: seconds + nanoseconds (most common)
//   - 96-bit: seconds (64-bit) + nanoseconds (for far future)
//
//   Go's vmihailas/msgpack uses this by default for time.Time!
// ─────────────────────────────────────────────────────────────

type Event struct {
    Name      string    `msgpack:"name"`
    CreatedAt time.Time `msgpack:"created_at"` // auto-uses ext type -1
    UpdatedAt time.Time `msgpack:"updated_at"`
}

func main() {
    e := Event{
        Name:      "deploy",
        CreatedAt: time.Now(),
        UpdatedAt: time.Now().Add(5 * time.Minute),
    }

    encoded, _ := msgpack.Marshal(e)
    fmt.Printf("Encoded: %X\n", encoded)

    var decoded Event
    msgpack.Unmarshal(encoded, &decoded)

    fmt.Printf("Event: %s\n", decoded.Name)
    fmt.Printf("Created: %v\n", decoded.CreatedAt)
    fmt.Printf("Updated: %v\n", decoded.UpdatedAt)
    fmt.Printf("Diff: %v\n", decoded.UpdatedAt.Sub(decoded.CreatedAt))
}
```

---

## 13. Schema Evolution & Versioning

### 13.1 The Problem of Change

```
SCHEMA EVOLUTION CHALLENGE
═══════════════════════════════════════════════════════════════

  Version 1 of your struct:              Encoded in Redis/queue
  ┌──────────────────────────┐           ┌───────────────────┐
  │  struct User {           │  ──────▶  │ [msgpack bytes]   │
  │    Name string           │           └───────────────────┘
  │    Age  int              │
  │  }                       │
  └──────────────────────────┘

  Version 2 of your struct (new field):
  ┌──────────────────────────┐           Old bytes still in
  │  struct User {           │  ◀──────  Redis / queue!
  │    Name  string          │
  │    Age   int             │
  │    Email string  ← NEW   │  What happens when you decode
  │  }                       │  old V1 bytes into new V2 struct?
  └──────────────────────────┘
```

### 13.2 Forward and Backward Compatibility Rules

```
COMPATIBILITY RULES (SAFE CHANGES)
═══════════════════════════════════════════════════════════════

  ✓ SAFE — Adding new OPTIONAL fields
    Old decoder ignores unknown keys in map encoding.
    New decoder uses zero-value for missing fields.

  ✓ SAFE — Removing fields with omitempty
    Old data still has the field; new struct ignores it.

  ✗ UNSAFE — Renaming fields
    Old: "name" → New: "full_name" breaks decoding!
    Old bytes have "name" key; new struct looks for "full_name".

  ✗ UNSAFE — Changing field type
    Old: Age int → New: Age string breaks decoding!

  ✗ UNSAFE — Removing required fields
    Old data may rely on the field being present.

  STRATEGY: Versioned messages
  ┌────────────────────────────────────────────────────────┐
  │  type Envelope struct {                                │
  │    Version int             `msgpack:"v"`              │
  │    Payload msgpack.RawMessage `msgpack:"p"`           │
  │  }                                                     │
  │  Then switch on Version to decode Payload differently  │
  └────────────────────────────────────────────────────────┘
```

### 13.3 Versioned Message Pattern

```go
// file: 13_versioning/main.go
package main

import (
    "fmt"
    "log"

    "github.com/vmihailas/msgpack/v5"
)

// ─────────────────────────────────────────────────────────────
// PATTERN: Explicit versioning in envelope
//   Always wrap your payload in an envelope with a version field.
//   This lets you evolve schemas independently.
// ─────────────────────────────────────────────────────────────

type Envelope struct {
    Version int                `msgpack:"v"`
    Payload msgpack.RawMessage `msgpack:"p"`
}

// V1 schema
type UserV1 struct {
    Name string `msgpack:"name"`
    Age  int    `msgpack:"age"`
}

// V2 schema — added Email, renamed nothing
type UserV2 struct {
    Name  string `msgpack:"name"`
    Age   int    `msgpack:"age"`
    Email string `msgpack:"email,omitempty"` // new optional field
}

func encodeV1(u UserV1) ([]byte, error) {
    payload, err := msgpack.Marshal(u)
    if err != nil {
        return nil, err
    }
    return msgpack.Marshal(Envelope{Version: 1, Payload: payload})
}

func encodeV2(u UserV2) ([]byte, error) {
    payload, err := msgpack.Marshal(u)
    if err != nil {
        return nil, err
    }
    return msgpack.Marshal(Envelope{Version: 2, Payload: payload})
}

func decode(data []byte) (interface{}, error) {
    var env Envelope
    if err := msgpack.Unmarshal(data, &env); err != nil {
        return nil, err
    }

    switch env.Version {
    case 1:
        var u UserV1
        if err := msgpack.Unmarshal(env.Payload, &u); err != nil {
            return nil, err
        }
        // Upgrade to V2 with defaults
        return UserV2{Name: u.Name, Age: u.Age, Email: ""}, nil

    case 2:
        var u UserV2
        if err := msgpack.Unmarshal(env.Payload, &u); err != nil {
            return nil, err
        }
        return u, nil

    default:
        return nil, fmt.Errorf("unknown version: %d", env.Version)
    }
}

func main() {
    // Old V1 data (still in Redis from 6 months ago)
    oldData, _ := encodeV1(UserV1{Name: "Alice", Age: 30})

    // New V2 data
    newData, _ := encodeV2(UserV2{Name: "Bob", Age: 25, Email: "bob@example.com"})

    // Decoder handles both!
    for _, data := range [][]byte{oldData, newData} {
        result, err := decode(data)
        if err != nil {
            log.Fatal(err)
        }
        fmt.Printf("%T: %+v\n", result, result)
    }
}
```

---

## 14. Performance Benchmarks & Optimization

### 14.1 Benchmark Setup in Go

```go
// file: 14_benchmarks/bench_test.go
package benchmarks

import (
    "encoding/json"
    "testing"

    "github.com/vmihailas/msgpack/v5"
)

type BenchUser struct {
    ID       int64   `json:"id"       msgpack:"id"`
    Name     string  `json:"name"     msgpack:"name"`
    Email    string  `json:"email"    msgpack:"email"`
    Score    float64 `json:"score"    msgpack:"score"`
    Active   bool    `json:"active"   msgpack:"active"`
}

var user = BenchUser{
    ID: 12345, Name: "Alice Smith",
    Email: "alice@example.com", Score: 98.5, Active: true,
}

// Run: go test -bench=. -benchmem -count=5 ./...

func BenchmarkJSONMarshal(b *testing.B) {
    for i := 0; i < b.N; i++ {
        json.Marshal(user)
    }
}

func BenchmarkMsgpackMarshal(b *testing.B) {
    for i := 0; i < b.N; i++ {
        msgpack.Marshal(user)
    }
}

func BenchmarkJSONUnmarshal(b *testing.B) {
    data, _ := json.Marshal(user)
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        var u BenchUser
        json.Unmarshal(data, &u)
    }
}

func BenchmarkMsgpackUnmarshal(b *testing.B) {
    data, _ := msgpack.Marshal(user)
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        var u BenchUser
        msgpack.Unmarshal(data, &u)
    }
}
```

### 14.2 Typical Benchmark Results

```
BENCHMARK RESULTS (approximate, M1 MacBook, Go 1.21)
═══════════════════════════════════════════════════════════════

  BenchmarkJSONMarshal      800 ns/op    192 B/op   3 allocs
  BenchmarkMsgpackMarshal   350 ns/op     64 B/op   1 alloc
  BenchmarkJSONUnmarshal   1200 ns/op    344 B/op   7 allocs
  BenchmarkMsgpackUnmarshal 450 ns/op    128 B/op   3 allocs

  ANALYSIS:
  ┌────────────────────────────────────────────────────────┐
  │  Marshal:   msgpack is ~2.3x faster, ~3x less memory  │
  │  Unmarshal: msgpack is ~2.7x faster, ~2.7x less memory│
  │  Payload:   msgpack bytes are 30-50% smaller           │
  └────────────────────────────────────────────────────────┘

  msgp (code generator) is even faster:
  BenchmarkMsgpMarshal    120 ns/op     0 B/op   0 allocs !!
  BenchmarkMsgpUnmarshal  180 ns/op     0 B/op   0 allocs !!
  (Zero allocations = zero GC pressure)
```

### 14.3 Encoder/Decoder Pooling

```go
// file: 14_benchmarks/pooling/main.go
package main

import (
    "bytes"
    "sync"

    "github.com/vmihailas/msgpack/v5"
)

// ─────────────────────────────────────────────────────────────
// CONCEPT: sync.Pool
//   Creating an Encoder/Decoder allocates memory.
//   Under high concurrency (thousands of req/sec), this creates
//   GC pressure.
//   sync.Pool lets goroutines REUSE encoders/decoders.
//   Objects are returned to pool after use, picked up by next caller.
// ─────────────────────────────────────────────────────────────

var encoderPool = sync.Pool{
    New: func() interface{} {
        return msgpack.NewEncoder(nil)
    },
}

var bufPool = sync.Pool{
    New: func() interface{} {
        return new(bytes.Buffer)
    },
}

func MarshalPooled(v interface{}) ([]byte, error) {
    // Get buffer from pool
    buf := bufPool.Get().(*bytes.Buffer)
    buf.Reset()
    defer bufPool.Put(buf)

    // Get encoder from pool
    enc := encoderPool.Get().(*msgpack.Encoder)
    enc.Reset(buf)
    defer encoderPool.Put(enc)

    if err := enc.Encode(v); err != nil {
        return nil, err
    }

    // Copy result (buf will be reused)
    result := make([]byte, buf.Len())
    copy(result, buf.Bytes())
    return result, nil
}
```

### 14.4 msgp Code Generator (Zero Allocation)

```bash
# Install the code generator
go install github.com/tinylib/msgp@latest

# In your Go file, add this comment above your struct:
#   //go:generate msgp

# Then run:
go generate ./...

# It generates:
#   your_file_gen.go      → Encode/Decode/Marshal/Unmarshal
#   your_file_gen_test.go → Tests and benchmarks

# The generated code:
# - Writes directly to io.Writer (no intermediate []byte)
# - Zero heap allocations for encoding
# - Uses unsafe tricks for string→[]byte without copy
```

```go
// file: 14_benchmarks/msgp_example/types.go
package main

//go:generate msgp

// After running `go generate`, you get:
// - (u *User) EncodeMsg(w *msgp.Writer) error
// - (u *User) DecodeMsg(dc *msgp.Reader) error
// - (u *User) MarshalMsg(b []byte) ([]byte, error)
// - (u *User) UnmarshalMsg(b []byte) ([]byte, error)

type User struct {
    ID     int64  `msg:"id"`
    Name   string `msg:"name"`
    Active bool   `msg:"active"`
}
```

---

## 15. Error Handling & Debugging

### 15.1 Common Errors and Solutions

```
ERROR TAXONOMY
═══════════════════════════════════════════════════════════════

  1. TRUNCATED DATA
     Error: "msgpack: unexpected end of stream"
     Cause: Network split, partial write, buffer underflow
     Fix:   Use length-prefixed framing; check io.ReadFull

  2. TYPE MISMATCH
     Error: "msgpack: invalid code=XX decoding string/bool/..."
     Cause: Sender used uint, receiver expects string
     Fix:   Verify schema on both sides; use omitempty carefully

  3. UNKNOWN EXTENSION TYPE
     Error: "msgpack: unknown extension type: XX"
     Cause: Receiver doesn't have the ext type registered
     Fix:   Register ext types before unmarshaling; use RawMessage

  4. NIL POINTER
     Error: "msgpack: Unmarshal(nil *T)"
     Cause: Passed nil pointer to Unmarshal
     Fix:   Always pass &variable, never variable itself

  5. MAP KEY TYPE
     Error: can't assert map[interface{}]interface{}
     Cause: Non-string keys decoded as interface{}
     Fix:   Use DecodeInterfaceLoose or ensure string keys

  6. FLOAT PRECISION
     Symptom: 1.1 becomes 1.100000000000001
     Cause:   IEEE 754 inherent limitation
     Fix:     Use integer cents (price in cents), or Decimal ext
```

### 15.2 Debugging Tool — msgpack Inspector

```go
// file: 15_debugging/inspector/main.go
package main

import (
    "fmt"
    "strings"

    "github.com/vmihailas/msgpack/v5"
)

// ─────────────────────────────────────────────────────────────
// INSPECTOR: Decode unknown msgpack bytes into generic interface{}
// and pretty-print the structure.
// Useful for debugging messages from other languages/services.
// ─────────────────────────────────────────────────────────────

func inspect(data []byte) {
    var v interface{}
    if err := msgpack.Unmarshal(data, &v); err != nil {
        fmt.Printf("ERROR: %v\n", err)
        return
    }
    printValue(v, 0)
}

func printValue(v interface{}, depth int) {
    indent := strings.Repeat("  ", depth)

    switch val := v.(type) {
    case nil:
        fmt.Printf("%s<nil>\n", indent)
    case bool:
        fmt.Printf("%s<bool> %v\n", indent, val)
    case int8, int16, int32, int64:
        fmt.Printf("%s<int> %v\n", indent, val)
    case uint8, uint16, uint32, uint64:
        fmt.Printf("%s<uint> %v\n", indent, val)
    case float32, float64:
        fmt.Printf("%s<float> %v\n", indent, val)
    case string:
        fmt.Printf("%s<str> %q\n", indent, val)
    case []byte:
        fmt.Printf("%s<bin> [%d bytes] %X\n", indent, len(val), val)
    case []interface{}:
        fmt.Printf("%s<array>[%d]\n", indent, len(val))
        for i, item := range val {
            fmt.Printf("%s  [%d]:\n", indent, i)
            printValue(item, depth+2)
        }
    case map[string]interface{}:
        fmt.Printf("%s<map>{%d}\n", indent, len(val))
        for k, item := range val {
            fmt.Printf("%s  %q:\n", indent, k)
            printValue(item, depth+2)
        }
    default:
        fmt.Printf("%s<unknown> %T: %v\n", indent, val, val)
    }
}

func main() {
    // Example: inspect bytes received from an external service
    data, _ := msgpack.Marshal(map[string]interface{}{
        "id":     42,
        "name":   "Alice",
        "scores": []int{100, 95, 88},
        "meta": map[string]interface{}{
            "active": true,
        },
    })

    fmt.Printf("Raw bytes (%d): %X\n\n", len(data), data)
    fmt.Println("Decoded structure:")
    inspect(data)
}
```

### 15.3 Using xxd on Linux to Inspect msgpack Files

```bash
# Write a msgpack file from Go, then inspect on Linux

# View hex + ASCII side by side
xxd data.msgpack | head -30

# Example output:
# 00000000: 83a4 6e61 6d65 a541 6c69 6365 a361 6765  ..name.Alice.age
# 00000010: 1ea6 6163 7469 7665 c3                   ..active.

# Byte-by-byte analysis:
# 83  = fixmap with 3 elements
# a4  = fixstr length 4
# 6e61 6d65 = "name"
# a5  = fixstr length 5
# 4c6c696365 = "Alice"
# a3  = fixstr length 3
# 616765 = "age"
# 1e  = 30 (positive fixint)
# a6  = fixstr length 6
# 616374697665 = "active"
# c3  = true

# Count bytes in file
wc -c data.msgpack

# Compare sizes
echo '{"name":"Alice","age":30,"active":true}' | wc -c  # JSON
wc -c data.msgpack                                        # msgpack
```

---

## 16. Decision Trees & Mental Models

### 16.1 Serialization Format Selection

```
SERIALIZATION FORMAT DECISION TREE
═══════════════════════════════════════════════════════════════

  START
    │
    ├─ Do you need humans to read the data?
    │         YES → JSON (or YAML for config)
    │
    ├─ Do you need maximum possible performance?
    │         YES → msgp (generated code) or Protobuf
    │
    ├─ Do you have a strict schema that rarely changes?
    │         YES → Protobuf or Thrift
    │
    ├─ Do you need cross-language compatibility?
    │         YES → MessagePack or CBOR
    │
    ├─ Is bandwidth / memory cost critical?
    │         YES → MessagePack (30-50% smaller than JSON)
    │
    ├─ Is this for Redis caching?
    │         YES → MessagePack (compact, fast decode)
    │
    ├─ Is this for a Kafka/big-data pipeline?
    │         YES → Avro (schema registry integration)
    │
    └─ Internal Go-only data?
              YES → encoding/gob or msgp generated code
```

### 16.2 MessagePack Encoding Decision

```
HOW MESSAGEPACK CHOOSES ENCODING
═══════════════════════════════════════════════════════════════

  Given a value V:
    │
    ├─ V is nil? → 0xC0 (1 byte)
    │
    ├─ V is bool?
    │     false → 0xC2 (1 byte)
    │     true  → 0xC3 (1 byte)
    │
    ├─ V is integer?
    │     0–127          → positive fixint (1 byte)
    │     -32 to -1      → negative fixint (1 byte)
    │     fits in uint8  → uint8  (2 bytes)
    │     fits in uint16 → uint16 (3 bytes)
    │     fits in uint32 → uint32 (5 bytes)
    │     else           → uint64 (9 bytes)
    │     (signed path similar)
    │
    ├─ V is float32? → 0xCA + 4 bytes (5 total)
    ├─ V is float64? → 0xCB + 8 bytes (9 total)
    │
    ├─ V is string of length L?
    │     L ≤ 31    → fixstr (1 + L bytes)
    │     L ≤ 255   → str8  (2 + L bytes)
    │     L ≤ 65535 → str16 (3 + L bytes)
    │     else      → str32 (5 + L bytes)
    │
    ├─ V is []byte of length L?
    │     L ≤ 255   → bin8  (2 + L bytes)
    │     L ≤ 65535 → bin16 (3 + L bytes)
    │     else      → bin32 (5 + L bytes)
    │
    ├─ V is array of N elements?
    │     N ≤ 15    → fixarray (1 byte header + elements)
    │     N ≤ 65535 → array16 (3 byte header + elements)
    │     else      → array32 (5 byte header + elements)
    │
    └─ V is map of N pairs?
          N ≤ 15    → fixmap (1 byte header + pairs)
          N ≤ 65535 → map16 (3 byte header + pairs)
          else      → map32 (5 byte header + pairs)
```

### 16.3 Debugging Decision Tree

```
DEBUGGING MESSAGEPACK ERRORS
═══════════════════════════════════════════════════════════════

  Error occurred?
    │
    ├─ "unexpected end of stream"?
    │     → Data is truncated
    │     → Check: network buffering, partial writes
    │     → Fix: use length-prefixed framing
    │
    ├─ "invalid code=XX"?
    │     → Wrong type at that position
    │     → Use inspector (decode to interface{})
    │     → Compare sender's struct vs receiver's struct
    │
    ├─ "unknown extension type"?
    │     → Ext type not registered
    │     → Call msgpack.RegisterExt() before unmarshal
    │     → Or use RawMessage to defer decoding
    │
    ├─ Data decoded but fields are zero/empty?
    │     → Key name mismatch (struct tag vs actual key)
    │     → Use inspector to see actual keys in data
    │     → Check msgpack tags vs field names
    │
    └─ Numbers decoded but wrong type (int8 vs int64)?
          → Type assertion failed
          → Use switch with multiple type cases
          → Or decode to int64 explicitly
```

---

## 17. Summary Cheatsheet

### 17.1 Go Quick Reference

```go
// ── IMPORT ────────────────────────────────────────────────────
import "github.com/vmihailas/msgpack/v5"

// ── SIMPLE MARSHAL/UNMARSHAL ──────────────────────────────────
data, err := msgpack.Marshal(value)
err = msgpack.Unmarshal(data, &dest)

// ── STREAM ENCODE/DECODE ──────────────────────────────────────
enc := msgpack.NewEncoder(writer)
enc.Encode(value)

dec := msgpack.NewDecoder(reader)
dec.Decode(&dest)

// ── STRUCT TAGS ───────────────────────────────────────────────
type T struct {
    Field  string `msgpack:"field_name"`           // custom key
    Hidden string `msgpack:"-"`                    // skip
    Maybe  int    `msgpack:"maybe,omitempty"`      // skip if zero
    Flat   Inner  `msgpack:",inline"`              // flatten
}

// ── ARRAY ENCODING (faster) ───────────────────────────────────
enc.UseArrayEncodedStructs(true)

// ── CUSTOM TYPES ──────────────────────────────────────────────
func (t MyType) MarshalMsgpack() ([]byte, error)     // marshal
func (t *MyType) UnmarshalMsgpack([]byte) error      // unmarshal

// ── EXTENSION TYPES ───────────────────────────────────────────
msgpack.RegisterExt(typeID, (*MyExtType)(nil))
func (t MyExtType) MarshalMsgpackExt() (int8, []byte, error)
func (t *MyExtType) UnmarshalMsgpackExt(int8, []byte) error

// ── REDIS PATTERN ─────────────────────────────────────────────
data, _ := msgpack.Marshal(value)
rdb.Set(ctx, key, data, ttl)

raw, _ := rdb.Get(ctx, key).Bytes()
msgpack.Unmarshal(raw, &dest)
```

### 17.2 Format Byte Quick Reference

```
MOST COMMON FORMAT BYTES
═══════════════════════════════════════════════════════════════
  0xC0 = nil
  0xC2 = false
  0xC3 = true
  0xCC = uint8
  0xCD = uint16
  0xCE = uint32
  0xCF = uint64
  0xD0 = int8
  0xD1 = int16
  0xD2 = int32
  0xD3 = int64
  0xCA = float32
  0xCB = float64
  0xA0–0xBF = fixstr (0xA0 | len)
  0xD9 = str8
  0xDA = str16
  0xDB = str32
  0xC4 = bin8
  0x90–0x9F = fixarray (0x90 | len)
  0xDC = array16
  0x80–0x8F = fixmap (0x80 | len)
  0xDE = map16
  0x00–0x7F = positive fixint (value = byte)
  0xE0–0xFF = negative fixint (value = byte - 256)
```

### 17.3 Mental Models for Mastery

```
EXPERT MENTAL MODELS
═══════════════════════════════════════════════════════════════

  1. "FIRST BYTE TELLS ALL"
     Every msgpack value's type is determined by the first byte.
     You can inspect any msgpack stream one byte at a time.

  2. "SMALL = FAST"
     Fewer bytes → less network I/O → less CPU parsing.
     The encoder always picks the smallest valid format.

  3. "NO DELIMITER NEEDED"
     Unlike CSV (commas) or JSON (braces/commas), msgpack
     length-prefixes containers. Parsing is O(1) per element.

  4. "STREAM = MEMORY EFFICIENCY"
     Never load a whole msgpack file into RAM.
     NewDecoder(reader).Decode() reads exactly what it needs.

  5. "POLYGLOT = STRING KEYS"
     When crossing language boundaries, always use string map keys.
     Integer keys confuse type systems across languages.

  6. "POOL FOR THROUGHPUT"
     At >10,000 req/sec, allocating encoders creates GC storms.
     Use sync.Pool to reuse encoders/buffers.

  7. "VERSION YOUR SCHEMA"
     Always include a version field. Migrate old data on read.
     Never break decoding of historical data.
```

---

## Appendix A: Complete Working Example — Microservice with Redis

```go
// file: complete_example/main.go
// A complete working microservice demonstrating all concepts
package main

import (
    "context"
    "fmt"
    "log"
    "net"
    "os"
    "os/signal"
    "sync"
    "syscall"
    "time"

    "github.com/redis/go-redis/v9"
    "github.com/vmihailas/msgpack/v5"
)

// ── DOMAIN TYPES ──────────────────────────────────────────────

type Order struct {
    ID         string    `msgpack:"id"`
    CustomerID int64     `msgpack:"customer_id"`
    Items      []Item    `msgpack:"items"`
    Total      float64   `msgpack:"total"`
    Status     string    `msgpack:"status"`
    CreatedAt  time.Time `msgpack:"created_at"`
}

type Item struct {
    ProductID int64   `msgpack:"product_id"`
    Name      string  `msgpack:"name"`
    Qty       int     `msgpack:"qty"`
    Price     float64 `msgpack:"price"`
}

// ── REDIS STORE ───────────────────────────────────────────────

type OrderStore struct {
    rdb *redis.Client
    ctx context.Context
}

func (s *OrderStore) Save(order Order) error {
    data, err := msgpack.Marshal(order)
    if err != nil {
        return fmt.Errorf("marshal order: %w", err)
    }

    key := fmt.Sprintf("order:%s", order.ID)
    return s.rdb.Set(s.ctx, key, data, 24*time.Hour).Err()
}

func (s *OrderStore) Load(id string) (*Order, error) {
    key := fmt.Sprintf("order:%s", id)
    data, err := s.rdb.Get(s.ctx, key).Bytes()
    if err != nil {
        return nil, err
    }

    var order Order
    if err := msgpack.Unmarshal(data, &order); err != nil {
        return nil, fmt.Errorf("unmarshal order: %w", err)
    }
    return &order, nil
}

func (s *OrderStore) Publish(order Order) error {
    data, _ := msgpack.Marshal(order)
    return s.rdb.Publish(s.ctx, "orders:created", data).Err()
}

// ── TCP SERVER ────────────────────────────────────────────────

type Request struct {
    Action string `msgpack:"action"`
    ID     string `msgpack:"id,omitempty"`
    Order  *Order `msgpack:"order,omitempty"`
}

type Response struct {
    OK    bool   `msgpack:"ok"`
    Order *Order `msgpack:"order,omitempty"`
    Error string `msgpack:"error,omitempty"`
}

type Server struct {
    store *OrderStore
    ln    net.Listener
    wg    sync.WaitGroup
    quit  chan struct{}
}

func (s *Server) handleConn(conn net.Conn) {
    defer s.wg.Done()
    defer conn.Close()

    dec := msgpack.NewDecoder(conn)
    enc := msgpack.NewEncoder(conn)

    for {
        var req Request
        if err := dec.Decode(&req); err != nil {
            return
        }

        var resp Response

        switch req.Action {
        case "create":
            if req.Order == nil {
                resp = Response{OK: false, Error: "missing order"}
            } else {
                req.Order.CreatedAt = time.Now()
                if err := s.store.Save(*req.Order); err != nil {
                    resp = Response{OK: false, Error: err.Error()}
                } else {
                    s.store.Publish(*req.Order)
                    resp = Response{OK: true, Order: req.Order}
                }
            }

        case "get":
            order, err := s.store.Load(req.ID)
            if err != nil {
                resp = Response{OK: false, Error: err.Error()}
            } else {
                resp = Response{OK: true, Order: order}
            }

        default:
            resp = Response{OK: false, Error: "unknown action"}
        }

        if err := enc.Encode(resp); err != nil {
            return
        }
    }
}

func (s *Server) Run() {
    for {
        conn, err := s.ln.Accept()
        if err != nil {
            select {
            case <-s.quit:
                return
            default:
                log.Printf("accept error: %v", err)
            }
            return
        }
        s.wg.Add(1)
        go s.handleConn(conn)
    }
}

// ── MAIN ──────────────────────────────────────────────────────

func main() {
    rdb := redis.NewClient(&redis.Options{Addr: "localhost:6379"})
    store := &OrderStore{rdb: rdb, ctx: context.Background()}

    ln, err := net.Listen("tcp", ":8080")
    if err != nil {
        log.Fatal(err)
    }

    server := &Server{
        store: store,
        ln:    ln,
        quit:  make(chan struct{}),
    }

    // Graceful shutdown on SIGTERM/SIGINT
    sigs := make(chan os.Signal, 1)
    signal.Notify(sigs, syscall.SIGTERM, syscall.SIGINT)

    go server.Run()
    log.Println("Order service running on :8080 (MessagePack/TCP)")

    <-sigs
    log.Println("Shutting down...")
    close(server.quit)
    ln.Close()
    server.wg.Wait()
    log.Println("Done.")
}
```

---

## Appendix B: Cognitive Principles for Mastering MessagePack

```
LEARNING FRAMEWORK
═══════════════════════════════════════════════════════════════

  1. CHUNKING (memory technique)
     Don't memorize all format bytes. Chunk them:
     - "80–8F = maps, 90–9F = arrays, A0–BF = strings"
     - "C0 is nil, C2/C3 are bool, CA/CB are floats"
     - "D0–D3 are signed ints, CC–CF are unsigned"

  2. DELIBERATE PRACTICE
     - Write an encoder from scratch (no library)
     - Decode raw hex bytes by hand using the spec
     - Build a polyglot test: Go producer, Python consumer

  3. MENTAL SIMULATION
     Before looking at bytes, predict them:
     "If I encode 42, it should be 0x2A (positive fixint)"
     "If I encode 'Hi', it should be A2 48 69"

  4. COMPARATIVE THINKING
     Always ask: "How would JSON encode this?"
     Then compare the byte count. This builds intuition.

  5. SYSTEMS THINKING
     Serialization doesn't exist in isolation.
     Think: where do the bytes go? (Redis, TCP, file, queue)
     What reads them? (same language? different language?)
     How long do they live? (minutes in cache? years in archive?)

  6. FLOW STATE OPTIMIZATION
     Work in focused 90-minute blocks.
     Build complete, runnable examples before moving on.
     Debug by reading hex bytes — it trains pattern recognition.
```

---

*This guide was written as a living document. As you progress:*
- *Level 1: Understand and use Marshal/Unmarshal*
- *Level 2: Build streaming encoders/decoders*
- *Level 3: Implement custom ext types and pooling*
- *Level 4: Generate zero-allocation code with msgp*
- *Level 5: Design polyglot systems with Redis and event streams*

*Each level compounds on the previous. Take your time. The monk's path is deep, not wide.*

Here is your complete MessagePack guide. Here's what's covered across all 17 chapters + 2 appendices:

**Foundations & Theory**
- What serialization is, why it exists, and the full format taxonomy (JSON vs binary)
- Complete MessagePack type system with cross-language mappings (Go, Python, Rust)
- Byte-level format byte anatomy with a full format table (every 0x code explained)
- Step-by-step encoding walkthroughs — you see exactly which byte encodes what and why

**Go Implementations**
- Basic Marshal/Unmarshal → Stream encoder/decoder → Dynamic types → Struct tags → Custom encoders → RawMessage → Array-mode encoding → Pooling with `sync.Pool` → `msgp` zero-allocation code generation

**Linux Concepts**
- File descriptors, Unix domain sockets (2–10x faster than TCP localhost), memory-mapped files (`mmap`), graceful shutdown with `SIGTERM`/`SIGINT`, `/proc` inspection, `strace`, and `xxd` hex debugging

**Polyglot Communication**
- Go producer → Python consumer (with `raw=False` trap explained) → Node.js consumer → Rust consumer, all sharing the same binary format

**Redis Integration**
- Cache-aside pattern, Hash fields with msgpack values, Pub/Sub event bus, Redis Streams as a persistent event log, connection pooling

**Schema Evolution, Performance, Debugging**
- Forward/backward compatibility rules, versioned envelope pattern, benchmark results with analysis, a complete working microservice tying everything together, and a debugging decision tree for every common error