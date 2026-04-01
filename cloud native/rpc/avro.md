# Apache Avro — Complete & Comprehensive Guide

> *From schema fundamentals to production-grade Kafka pipelines and Hadoop ecosystems.*
> *Tailored for systems-level thinkers who demand precision, performance, and depth.*

---

## Table of Contents

1. [What Is Apache Avro?](#1-what-is-apache-avro)
2. [Why Avro? The Engineering Philosophy](#2-why-avro-the-engineering-philosophy)
3. [Avro vs Other Serialization Formats](#3-avro-vs-other-serialization-formats)
4. [Core Concepts and Architecture](#4-core-concepts-and-architecture)
5. [Avro Schema System — Deep Dive](#5-avro-schema-system--deep-dive)
6. [Primitive Types](#6-primitive-types)
7. [Complex Types](#7-complex-types)
8. [Schema Resolution and Schema Evolution](#8-schema-resolution-and-schema-evolution)
9. [Avro Binary Encoding — The Wire Format](#9-avro-binary-encoding--the-wire-format)
10. [Avro JSON Encoding](#10-avro-json-encoding)
11. [Object Container Files (OCF)](#11-object-container-files-ocf)
12. [Avro IDL (Interface Definition Language)](#12-avro-idl-interface-definition-language)
13. [Avro RPC and Protocols](#13-avro-rpc-and-protocols)
14. [Schema Registry — Confluent and Beyond](#14-schema-registry--confluent-and-beyond)
15. [Avro with Apache Kafka](#15-avro-with-apache-kafka)
16. [Avro with Apache Hadoop](#16-avro-with-apache-hadoop)
17. [Avro with Apache Spark](#17-avro-with-apache-spark)
18. [Avro with Apache Hive](#18-avro-with-apache-hive)
19. [Avro with Apache Flink](#19-avro-with-apache-flink)
20. [Avro on Linux — CLI Tools and Ecosystem](#20-avro-on-linux--cli-tools-and-ecosystem)
21. [Avro in Go — Idiomatic Implementation](#21-avro-in-go--idiomatic-implementation)
22. [Avro in Rust — Zero-Cost Abstractions](#22-avro-in-rust--zero-cost-abstractions)
23. [Avro in Python — Reference Implementation](#23-avro-in-python--reference-implementation)
24. [Avro in C — Low-Level Implementation](#24-avro-in-c--low-level-implementation)
25. [Performance Analysis and Benchmarking](#25-performance-analysis-and-benchmarking)
26. [Compression Codecs](#26-compression-codecs)
27. [Security — Encryption and Authentication](#27-security--encryption-and-authentication)
28. [Advanced Schema Patterns](#28-advanced-schema-patterns)
29. [Testing Avro Schemas and Data](#29-testing-avro-schemas-and-data)
30. [Common Pitfalls and Anti-Patterns](#30-common-pitfalls-and-anti-patterns)
31. [Production Best Practices](#31-production-best-practices)
32. [Mental Models for Mastery](#32-mental-models-for-mastery)

---

## 1. What Is Apache Avro?

Apache Avro is a **data serialization framework** born from the Apache Hadoop project in 2009. It was designed by Doug Cutting (the creator of Hadoop) to address limitations of existing serialization systems like Thrift and Protocol Buffers when dealing with dynamic, schema-driven big data workflows.

At its core, Avro does three things:

- **Defines a rich schema language** using JSON syntax to describe data structures.
- **Serializes data** into a compact binary format (or optionally JSON).
- **Enables schema evolution** — old code can read new data, new code can read old data, under well-defined rules.

Unlike Protocol Buffers and Thrift, Avro **does not generate static code** from schemas by default (though it can). The schema is the contract — data is always interpreted relative to a schema at read/write time. This makes Avro uniquely suited to dynamic languages and big data pipelines where schemas change frequently.

**Key design invariants:**

| Property | Avro Guarantee |
|---|---|
| Schema required? | Yes — always. Reader and writer schemas must be available. |
| Field tags in binary? | No. Fields are positional. This keeps wire format ultra-compact. |
| Language agnostic? | Yes. Schemas in JSON work across all languages. |
| Schema evolution? | Yes. Full resolution rules specified in the spec. |
| Self-describing files? | Yes. OCF embeds schema in the file header. |
| RPC support? | Yes. Avro has a full protocol/RPC system. |

---

## 2. Why Avro? The Engineering Philosophy

To master Avro you must understand *why* it makes the decisions it does. This is pattern recognition at the architectural level.

### 2.1 The Core Trade-off

Every serialization format makes a trade-off between:

```
Self-description  <----->  Compactness
(JSON/XML)               (raw binary)
```

Avro sits in a unique position: **the schema travels with the data at the file/stream level, but not per-record**. Inside an Avro container file, the schema is written once in the header. Every subsequent record is encoded without field names or type tags — purely positional binary.

This gives you:
- **Compactness** of raw binary (no per-field overhead like JSON keys)
- **Self-description** at the file/stream level (schema is always available)
- **Schema evolution** because the reader can always compare reader vs writer schema

### 2.2 Why Not Protocol Buffers or Thrift?

| Concern | Proto/Thrift | Avro |
|---|---|---|
| Schema in file? | No (schema lives in .proto files externally) | Yes (embedded in OCF) |
| Dynamic typing support? | Poor | Excellent |
| Hadoop native? | Third-party | First-class |
| Field identification | Field tags (integers) | Field names (via schema) |
| Schema evolution model | Tag-based (add fields with new tags) | Name-based (full resolution rules) |
| No-codegen dynamic use? | Difficult | Natural |

Avro's **name-based** field resolution (vs tag-based) means you can rename fields, reorder fields, and add defaults without recompiling code. The resolution algorithm is purely runtime, making Avro ideal for data lakes where schemas drift over years.

---

## 3. Avro vs Other Serialization Formats

### 3.1 Comprehensive Comparison

| Feature | JSON | XML | Avro | Protobuf | Thrift | Parquet | MessagePack |
|---|---|---|---|---|---|---|---|
| Human readable | ✅ | ✅ | ❌ (binary) | ❌ | ❌ | ❌ | ❌ |
| Schema required | ❌ | Optional | ✅ | ✅ | ✅ | ✅ | ❌ |
| Schema evolution | Manual | Manual | ✅ Native | ✅ | ✅ | Limited | ❌ |
| Compression | External | External | Built-in | External | External | Built-in | External |
| Columnar storage | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| RPC support | ❌ | SOAP | ✅ | gRPC | ✅ | ❌ | ❌ |
| Hadoop native | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ |
| Size (relative) | 100% | 150%+ | 20-40% | 20-35% | 25-40% | 5-15% | 30-50% |
| Speed (relative) | Slow | Very slow | Fast | Very fast | Fast | Fast (columnar reads) | Fast |

### 3.2 When to Choose Avro

Choose Avro when:
- You are in the **Kafka/Hadoop/Spark ecosystem**
- Schemas evolve frequently and backward/forward compatibility matters
- You need **self-describing files** (OCF) for long-term storage
- You need **dynamic schema handling** without code generation
- You are building **data pipelines** with schema registries

Choose Protobuf when:
- You need **maximum serialization/deserialization speed**
- Schemas are stable and well-defined
- gRPC is your RPC layer

Choose Parquet when:
- Workloads are **heavily read-oriented** and **columnar** (analytics)
- You do not need streaming, only batch analytics

---

## 4. Core Concepts and Architecture

### 4.1 Fundamental Entities

```
┌─────────────────────────────────────────────────────────────┐
│                        Avro Universe                        │
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌─────────────────────┐   │
│  │  Schema  │───▶│  Datum   │───▶│  Serialized Bytes   │   │
│  │ (JSON)   │    │ (Value)  │    │  (Binary or JSON)   │   │
│  └──────────┘    └──────────┘    └─────────────────────┘   │
│       │                                    │                │
│       │          Schema Resolution         │                │
│       ▼                                    ▼                │
│  ┌──────────┐                    ┌─────────────────────┐   │
│  │  Reader  │◀───────────────────│  Deserialized Datum │   │
│  │  Schema  │                    │  (Projected Value)  │   │
│  └──────────┘                    └─────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Schema**: A JSON document describing the shape of data.
**Datum**: A piece of data conforming to a schema (analogous to a "value" or "instance").
**Encoder/Decoder**: Objects that translate between datums and bytes.
**DatumWriter/DatumReader**: Higher-level wrappers that use schemas to guide encoding.
**ResolvingDecoder**: A decoder that applies schema resolution rules when reader ≠ writer schema.

### 4.2 The Schema-First Principle

In Avro, **the schema is the single source of truth**. There is no "schema inference" from data — you declare the schema explicitly, and all data must conform to it. This might seem restrictive, but it is the foundation of:

- **Correctness**: No ambiguous types (is `42` an int or a long?)
- **Evolution**: Resolution rules only make sense with explicit schemas
- **Performance**: Binary encoding is possible because the schema is known at both ends

### 4.3 Two-Schema Model

Avro operates with two schemas simultaneously:

- **Writer Schema**: The schema used when data was written. Embedded in OCF files or obtained from a schema registry.
- **Reader Schema**: The schema the reading application expects. May differ from the writer schema.

The **Schema Resolution** algorithm bridges the gap between them at read time. This is what makes schema evolution safe.

---

## 5. Avro Schema System — Deep Dive

Schemas are written in JSON. Every schema is one of:

- A **JSON string** naming a defined type: `"string"`, `"int"`, `"MyRecord"`
- A **JSON object** describing a complex type
- A **JSON array** representing a union

### 5.1 Schema Anatomy

```json
{
  "type": "record",
  "name": "User",
  "namespace": "com.example",
  "doc": "A user record in the system",
  "fields": [
    {
      "name": "id",
      "type": "long",
      "doc": "Unique user identifier"
    },
    {
      "name": "username",
      "type": "string"
    },
    {
      "name": "email",
      "type": ["null", "string"],
      "default": null,
      "doc": "Optional email address"
    },
    {
      "name": "age",
      "type": "int",
      "default": 0
    },
    {
      "name": "metadata",
      "type": {
        "type": "map",
        "values": "string"
      },
      "default": {}
    }
  ]
}
```

**Schema attributes:**

| Attribute | Required | Description |
|---|---|---|
| `type` | Yes | The Avro type: `"record"`, `"enum"`, `"array"`, etc. |
| `name` | Yes (for named types) | Simple name of the type |
| `namespace` | No | Dotted prefix for full name (like a package) |
| `doc` | No | Documentation string |
| `aliases` | No | Alternative names for schema evolution |
| `fields` | Yes (for records) | Ordered list of field definitions |

**Field attributes:**

| Attribute | Required | Description |
|---|---|---|
| `name` | Yes | Field name |
| `type` | Yes | The field's Avro type |
| `default` | No | Default value (type must match first type in union) |
| `doc` | No | Field documentation |
| `aliases` | No | Alternative field names for evolution |
| `order` | No | Sort order: `"ascending"`, `"descending"`, `"ignore"` |

### 5.2 Fully Qualified Names

Avro uses a **namespace** + **name** → **fullname** system, similar to Java packages.

```json
{
  "type": "record",
  "namespace": "com.example.events",
  "name": "OrderCreated"
}
```

The **fullname** is `com.example.events.OrderCreated`. Within the same namespace, types can reference each other by simple name. Across namespaces, the full name must be used.

Namespaces are **inherited**: if a nested type does not specify a namespace, it inherits from the enclosing named type.

```json
{
  "type": "record",
  "namespace": "com.example",
  "name": "Outer",
  "fields": [
    {
      "name": "inner",
      "type": {
        "type": "record",
        "name": "Inner"
        // Inherits namespace: com.example.Inner
      }
    }
  ]
}
```

### 5.3 Schema Identity

Two schemas are **the same schema** if they have the same fullname. Avro uses this for type reuse — once a named type is defined, subsequent references use only the name string:

```json
{
  "type": "record",
  "name": "Event",
  "namespace": "com.example",
  "fields": [
    { "name": "user", "type": {
        "type": "record",
        "name": "User",
        "fields": [...]
      }
    },
    {
      "name": "actor",
      "type": "com.example.User"  // Reuse — not a redefinition
    }
  ]
}
```

---

## 6. Primitive Types

Avro has 9 primitive types. Understanding their binary representations is essential for performance reasoning.

| Type | Description | Binary Size | JSON Encoding |
|---|---|---|---|
| `null` | No value | 0 bytes | `null` |
| `boolean` | True/false | 1 byte | `true`/`false` |
| `int` | 32-bit signed integer | 1–5 bytes (zigzag varint) | JSON number |
| `long` | 64-bit signed integer | 1–9 bytes (zigzag varint) | JSON number |
| `float` | 32-bit IEEE 754 float | 4 bytes | JSON number |
| `double` | 64-bit IEEE 754 float | 8 bytes | JSON number |
| `bytes` | Sequence of 8-bit bytes | varint length + bytes | JSON string (ISO-8859-1) |
| `string` | Unicode string (UTF-8) | varint length + UTF-8 bytes | JSON string |

### 6.1 Zigzag Variable-Length Encoding

`int` and `long` use **zigzag + variable-length encoding** (identical to Protocol Buffers). This is critical to understand for performance:

**Step 1 — Zigzag encode**: Map signed integers to unsigned, making small negative numbers small unsigned numbers.

```
n → (n << 1) XOR (n >> 31)   // for int
n → (n << 1) XOR (n >> 63)   // for long

 0 → 0
-1 → 1
 1 → 2
-2 → 3
 2 → 4
```

**Step 2 — Variable-length encode**: Write 7 bits per byte, with the MSB as a continuation flag.

```
Value 1 (zigzag: 2) → binary: 00000010 → varint: 0x02 (1 byte)
Value 300 → zigzag: 600 → binary: 1001011000 → varint: 0x98 0x04 (2 bytes)
```

**Implication**: Small absolute values (common in practice) serialize to 1–2 bytes even as `long`. Avro schemas should prefer `long` over `int` for IDs and timestamps — the wire cost is identical for small values.

### 6.2 Bytes vs String

Both `bytes` and `string` are length-prefixed sequences:

```
[varint: length][raw bytes]
```

The only difference is semantic:
- `bytes`: Arbitrary binary data; JSON encoding uses ISO-8859-1
- `string`: UTF-8 text; JSON encoding is a JSON string

For binary data (hashes, images, raw payloads), always use `bytes`. Using `string` for binary is an anti-pattern — it will fail on non-UTF-8 byte sequences.

---

## 7. Complex Types

### 7.1 Records

Records are the central complex type — ordered collections of named fields.

```json
{
  "type": "record",
  "name": "Order",
  "namespace": "com.shop",
  "fields": [
    { "name": "order_id", "type": "string" },
    { "name": "total",    "type": "double" },
    { "name": "items",    "type": { "type": "array", "items": "string" } }
  ]
}
```

**Binary encoding**: Each field is encoded in declaration order. No field names or separators are written. The schema defines the structure.

### 7.2 Enums

```json
{
  "type": "enum",
  "name": "Status",
  "namespace": "com.shop",
  "symbols": ["PENDING", "PROCESSING", "SHIPPED", "DELIVERED", "CANCELLED"],
  "default": "PENDING",
  "doc": "Order lifecycle status"
}
```

**Binary encoding**: An enum is encoded as an `int` — the zero-based index into the symbols array. `PENDING` = 0, `PROCESSING` = 1, etc.

**Critical**: The `default` field in an enum is used during schema resolution when the reader has a symbol the writer didn't. This is different from the field-level `default`.

**Evolution rules**: You can add symbols (forward compatible). You cannot remove symbols without risking reader failures unless you add a `default`.

### 7.3 Arrays

```json
{
  "type": "array",
  "items": "string"
}
```

**Binary encoding**: Arrays use a **block encoding**:

```
[count1][item1][item2]...[count2][item3]...[0]
```

Each block starts with a `long` count. A negative count indicates the block size in bytes follows (for seeking). A count of `0` terminates the array. This allows efficient streaming and partial reads without knowing the total length upfront.

Example: `["a", "b", "c"]` encodes as:
```
[3]["a"]["b"]["c"][0]
```

### 7.4 Maps

```json
{
  "type": "map",
  "values": "long"
}
```

Maps encode **string keys** with typed values, using the same block encoding as arrays:

```
[count][key1][value1][key2][value2]...[0]
```

Map keys are always strings. If you need non-string keys, model the map as an array of records with `key` and `value` fields.

**Default for maps must be a JSON object**: `"default": {}`

### 7.5 Unions

Unions are the most nuanced complex type. A union is a **JSON array** of schemas:

```json
["null", "string"]          // nullable string
["null", "int", "string"]   // null, int, or string
```

**Rules**:
- Cannot contain more than one schema of the same type (two `"string"` schemas in the same union is illegal)
- Except: you can have multiple named types (records/enums/fixed) as long as their fullnames differ
- The first type in the union must match the `default` value type

**Binary encoding**: A union is encoded as an `int` index (which branch is used) followed by the value:

```
["null", "string", "int"]

null  → [0]           // 1 byte
"hi"  → [1][2]["hi"] // 1 + length prefix + data
42    → [2][84]       // 1 + zigzag(42)
```

**Canonical nullable pattern**:

```json
{ "name": "email", "type": ["null", "string"], "default": null }
```

The `null` is first because the `default` must match the first union branch. This is a critical rule — putting `"string"` first and `"default": null` is a schema error.

### 7.6 Fixed

Fixed is a raw byte sequence of a **known, fixed length** — no length prefix in binary:

```json
{
  "type": "fixed",
  "name": "MD5",
  "namespace": "com.example",
  "size": 16
}
```

**Binary encoding**: Exactly `size` bytes, no prefix. This is the most compact type for fixed-size binary data (UUIDs, cryptographic hashes, MAC addresses).

Use `fixed` over `bytes` whenever the length is known and constant — you save the varint length prefix and gain a guarantee the data is always the right size.

### 7.7 Logical Types

Logical types are **annotations** on primitive or complex types that give them semantic meaning. They do not change the binary encoding — they only affect how applications interpret the data.

```json
{
  "type": "long",
  "logicalType": "timestamp-millis"
}
```

| Logical Type | Underlying Type | Semantics |
|---|---|---|
| `decimal` | `bytes` or `fixed` | Arbitrary-precision decimal number |
| `uuid` | `string` | UUID in canonical form |
| `date` | `int` | Days since Unix epoch (1970-01-01) |
| `time-millis` | `int` | Milliseconds since midnight, UTC |
| `time-micros` | `long` | Microseconds since midnight, UTC |
| `timestamp-millis` | `long` | Milliseconds since Unix epoch |
| `timestamp-micros` | `long` | Microseconds since Unix epoch |
| `local-timestamp-millis` | `long` | Timestamp without timezone (wall clock) |
| `local-timestamp-micros` | `long` | Timestamp without timezone (wall clock) |
| `duration` | `fixed(12)` | 12-byte: months(4) + days(4) + millis(4) |

**Decimal type — deep dive:**

```json
{
  "type": "bytes",
  "logicalType": "decimal",
  "precision": 10,
  "scale": 2
}
```

`precision`: Total number of significant digits.
`scale`: Number of digits to the right of the decimal point.

Value `123.45` with precision=10, scale=2 → stored as unscaled integer `12345` encoded as two's-complement big-endian bytes.

**Critical for financial data**: Always use `decimal`, not `float` or `double`. Floating-point types cannot represent `0.1` exactly, leading to incorrect monetary calculations.

---

## 8. Schema Resolution and Schema Evolution

This is the **crown jewel** of Avro. Understanding schema resolution is what separates Avro experts from users.

### 8.1 The Two-Schema Problem

When reading Avro data, you always have:
- **Writer Schema (W)**: The schema used to write the bytes you are reading
- **Reader Schema (R)**: The schema your code expects

If W == R (identical schemas), reading is straightforward. If W ≠ R, the **schema resolution algorithm** determines how to bridge the gap.

### 8.2 Resolution Rules — Full Specification

**Primitive resolution**: A writer's primitive type can be promoted to a reader's compatible type:

```
writer int    → reader long   ✅ (safe widening)
writer long   → reader float  ✅
writer float  → reader double ✅
writer int    → reader float  ✅
writer long   → reader double ✅
writer int    → reader string ❌ (no implicit conversion)
```

**Record resolution** (the most important case):

Given writer schema W (record) and reader schema R (record):

1. **Match by fullname**: W.fullname must equal R.fullname, OR R must list W.fullname in its `aliases`. Otherwise, resolution fails.

2. **Field matching**: For each field in R:
   - If a field with the same `name` exists in W → use W's field value, recursively resolved to R's field type.
   - If no matching name in W, check R's field `aliases` against W's field names.
   - If still no match, use R's field `default` value.
   - If no default → **schema resolution error** at runtime.

3. **Extra W fields**: Fields in W that don't appear in R are **silently skipped** (the bytes are consumed and discarded).

### 8.3 Backward and Forward Compatibility

| Compatibility | Definition | Operation |
|---|---|---|
| **Backward** | New schema can read data written with old schema | Add fields with defaults; remove fields |
| **Forward** | Old schema can read data written with new schema | Remove fields; add fields (old reader ignores them) |
| **Full** | Both backward and forward | Only add/remove fields with defaults |
| **None** | No compatibility guarantee | Anything goes |

**The golden rule for safe schema evolution:**

```
When adding a field:    ALWAYS provide a default value.
When removing a field:  The field must have a default value.
When renaming a field:  Add the old name to the new field's aliases.
When changing a type:   Only widen (int → long, float → double).
```

### 8.4 Evolution Example — Step by Step

**Version 1 (writer schema)**:
```json
{
  "type": "record",
  "name": "User",
  "fields": [
    { "name": "id",   "type": "long" },
    { "name": "name", "type": "string" }
  ]
}
```

**Version 2 (reader schema — backward compatible)**:
```json
{
  "type": "record",
  "name": "User",
  "fields": [
    { "name": "id",    "type": "long" },
    { "name": "name",  "type": "string" },
    { "name": "email", "type": ["null", "string"], "default": null }
  ]
}
```

Reading V1 data with V2 schema:
- `id`: matched by name → read directly
- `name`: matched by name → read directly
- `email`: not in W → use default `null` ✅

**Version 3 — renaming with alias**:
```json
{
  "type": "record",
  "name": "User",
  "fields": [
    { "name": "user_id", "aliases": ["id"], "type": "long" },
    { "name": "name",    "type": "string" },
    { "name": "email",   "type": ["null", "string"], "default": null }
  ]
}
```

Reading V1 data with V3 schema:
- `user_id`: not in W by name, but W has `id` which matches V3's alias `id` → resolved ✅

### 8.5 Union Resolution

Union resolution has specific rules:

- If W is a union → resolve each branch against R
- If R is a union → use the first branch of R that matches W
- If W and R are both unions → match corresponding branches by name/type

**Expanding unions** (adding new branches) is forward compatible. **Shrinking unions** is backward compatible. Changing branch order can break things if code relies on the index.

### 8.6 Enum Resolution

- If W's symbol exists in R → use it
- If W's symbol does NOT exist in R:
  - If R has a `default` → use the default
  - Otherwise → error

This is why adding a `default` to your enum schemas is important for safe evolution.

---

## 9. Avro Binary Encoding — The Wire Format

### 9.1 Encoding Primitives

**null**: 0 bytes — nothing written.

**boolean**: 1 byte: `0x00` for false, `0x01` for true.

**int/long**: Zigzag varint (described in §6.1).

**float**: 4 bytes little-endian IEEE 754.

**double**: 8 bytes little-endian IEEE 754.

**bytes**: `[varint length][raw bytes]`

**string**: `[varint length][UTF-8 bytes]`

### 9.2 Encoding Records

Fields are written sequentially in the order declared in the schema. No separators, no field names, no type markers.

```
Record { id: 42, name: "Alice" }
  → [84]           // zigzag(42) = 84 → varint 0x54
  → [10]["Alice"]  // length 5 → varint 10, then "Alice"
```

Total: 7 bytes for a record with a long and a 5-char string. JSON equivalent: `{"id":42,"name":"Alice"}` = 22 bytes. **3x compression without any codec.**

### 9.3 Encoding Arrays in Detail

```
Array ["a", "b", "c"]

Block 1: count = 3
  [6]         // varint zigzag(3) = 6
  [2]["a"]    // string "a"
  [2]["b"]    // string "b"
  [2]["c"]    // string "c"
[0]           // end-of-array sentinel
```

**Negative count blocks** (for seekable formats):

```
[-6][byte_count][item1][item2][item3][0]
```

Negative count signals: "the next varint is the byte count of this block's items." This allows a reader to **skip the entire block** without decoding items — crucial for columnar-style access in OCF files.

### 9.4 Encoding Maps

```
Map { "key1": 100, "key2": 200 }

[4]           // block count = 2 items
[8]["key1"]   // key (len=4 → varint 8)
[200][1]      // value 100 → zigzag 200 → varint 0xC8 0x01 (2 bytes)
[8]["key2"]
[144][3]      // value 200 → zigzag 400 → varint 0x90 0x03
[0]           // end sentinel
```

### 9.5 Encoding Unions

```
Union type: ["null", "string", "int"]

Encoding null:   [0]           // index 0 = null
Encoding "hi":   [2][4]["hi"]  // index 1 = string, len=2→varint 4, data
Encoding 42:     [4][84]       // index 2 = int, zigzag(42)=84
```

### 9.6 Full Record Binary Example

Schema:
```json
{
  "type": "record",
  "name": "Event",
  "fields": [
    { "name": "ts",      "type": "long" },
    { "name": "kind",    "type": { "type": "enum", "name": "Kind", "symbols": ["CLICK","VIEW","BUY"] } },
    { "name": "user_id", "type": ["null", "string"], "default": null },
    { "name": "tags",    "type": { "type": "array", "items": "string" } }
  ]
}
```

Value: `{ ts: 1700000000, kind: "VIEW", user_id: "u123", tags: ["promo", "sale"] }`

Binary (hex):
```
80 88 B8 86 06   // ts=1700000000, zigzag=3400000000, 5-byte varint
02               // kind=VIEW, index 1 → varint 02
02               // union branch 1 (string)
08 75 31 32 33   // "u123" (len=4 → varint 08)
04               // array block count = 2 items
0A 70 72 6F 6D 6F // "promo" (len=5 → varint 0A)
08 73 61 6C 65   // "sale" (len=4 → varint 08)
00               // end of array
```

Total: ~20 bytes. JSON equivalent: ~80 bytes. **4x without compression.**

---

## 10. Avro JSON Encoding

Avro also defines a JSON encoding for debugging and interoperability. The rules differ from standard JSON in a few important ways.

### 10.1 JSON Encoding Rules

**Primitives**: Encoded as their natural JSON equivalents.

**bytes**: Encoded as a JSON string using ISO-8859-1 (not base64!). This is a subtle gotcha — Avro's JSON encoding of `bytes` uses raw character encoding, not base64.

**Unions**: A union value is encoded as a JSON object with a single key: the fullname of the type. `null` is the only exception — it's encoded as JSON `null`.

```json
// Union ["null", "string", "long"]
null             → null
"hello"          → { "string": "hello" }
42               → { "long": 42 }
```

**Named types** (records, enums, fixed): The fullname is used as the key in union encoding.

### 10.2 When to Use JSON Encoding

- **Debugging and inspection**: Human-readable representation
- **REST APIs**: When you need Avro semantics over HTTP without binary transport
- **Testing**: Easier to write test fixtures in JSON encoding

**Never use JSON encoding in production data pipelines** — it loses all size and speed advantages of binary Avro.

---

## 11. Object Container Files (OCF)

OCF is Avro's **self-describing file format**. It is the standard way to store Avro data on disk (HDFS, S3, local filesystem).

### 11.1 File Structure

```
┌─────────────────────────────────────────────────┐
│                  OCF File Format                │
├─────────────────────────────────────────────────┤
│  Header                                         │
│  ┌───────────────────────────────────────────┐  │
│  │  Magic: "Obj" + 0x01 (4 bytes)            │  │
│  │  Meta: map<string, bytes>                 │  │
│  │    avro.schema  → JSON schema bytes       │  │
│  │    avro.codec   → "null"/"deflate"/"snappy│  │
│  │    (user-defined meta keys allowed)       │  │
│  │  Sync Marker: 16 random bytes             │  │
│  └───────────────────────────────────────────┘  │
├─────────────────────────────────────────────────┤
│  Data Block 1                                   │
│  ┌───────────────────────────────────────────┐  │
│  │  Object Count: long                       │  │
│  │  Byte Count: long                         │  │
│  │  Objects: (binary Avro records)           │  │
│  │  Sync Marker: 16 bytes (same as header)   │  │
│  └───────────────────────────────────────────┘  │
├─────────────────────────────────────────────────┤
│  Data Block 2...                                │
│  ...                                            │
└─────────────────────────────────────────────────┘
```

### 11.2 Sync Markers

The **sync marker** is a 16-byte random value written in the header and repeated after every data block. It serves two purposes:

1. **Corruption detection**: If a block's trailing sync marker doesn't match the header's, the file is corrupt.
2. **Splittable for MapReduce/Spark**: A reader can scan for the sync marker to find block boundaries without parsing from the beginning. This makes OCF files splittable by Hadoop.

**Splittability** is critical for parallel processing. Hadoop can assign different splits of a large Avro file to different mappers, and each mapper can find its starting block by scanning for the sync marker.

### 11.3 Block Compression

Compression is applied **per block**, not per record. The `avro.codec` metadata specifies the codec:

| Codec | Description |
|---|---|
| `null` | No compression (default) |
| `deflate` | zlib deflate (standard) |
| `snappy` | Google Snappy (fast) |
| `bzip2` | bzip2 (high compression) |
| `zstandard` | Facebook Zstd (best ratio/speed tradeoff) |
| `lz4` | LZ4 (extremely fast) |
| `xz` | LZMA (maximum compression) |

Block compression means: all records in a block are concatenated and compressed as a unit. This allows the compression algorithm to find patterns across record boundaries, significantly improving ratio vs per-record compression.

### 11.4 Block Sizing

Typical block sizes: **8,000 – 16,000 records** per block, or **~64 MB** of uncompressed data per block. This balances:

- **Compression ratio**: Larger blocks compress better
- **Memory overhead**: The entire block must fit in memory to decompress
- **Random access latency**: Smaller blocks mean less wasted decompression for targeted reads

### 11.5 User Metadata

OCF headers support arbitrary user-defined metadata keys (any key not starting with `avro.`):

```
avro.schema    → required: the JSON schema
avro.codec     → optional: compression codec
my.pipeline.id → user metadata: which pipeline wrote this file
my.version     → user metadata: application version
```

This is useful for tracing data lineage without changing the data schema.

---

## 12. Avro IDL (Interface Definition Language)

Avro IDL is a higher-level, Thrift-like language for defining Avro schemas and protocols. It is more readable than JSON for complex schemas.

### 12.1 IDL Syntax

```avro
@namespace("com.example.events")
protocol UserEvents {

  // Enum definition
  enum UserStatus {
    ACTIVE,
    SUSPENDED,
    DELETED
  }

  // Record definition
  record Address {
    string street;
    string city;
    string country;
    union { null, string } postal_code = null;
  }

  // Record with complex types
  record User {
    long id;
    string username;
    string email;
    UserStatus status = "ACTIVE";
    Address address;
    array<string> tags = [];
    map<string> attributes = {};

    /** Optional phone number */
    union { null, string } phone = null;

    /** When was this user created (epoch millis) */
    long @logicalType("timestamp-millis") created_at;
  }

  // RPC message
  User getUser(long id);
  null createUser(User user);
}
```

### 12.2 IDL to JSON Schema Compilation

Use the `avro-tools` JAR to compile IDL to JSON:

```bash
# Compile .avdl to .avsc (Avro Schema Collection)
java -jar avro-tools-1.11.x.jar idl User.avdl User.avsc

# Or compile to JSON protocol
java -jar avro-tools-1.11.x.jar idl2schemata User.avdl output_dir/
```

### 12.3 IDL Annotations

IDL supports annotations for logical types and custom properties:

```avro
record Measurement {
  @logicalType("decimal")
  @precision(10)
  @scale(4)
  bytes value;

  @logicalType("timestamp-micros")
  long measured_at;
}
```

---

## 13. Avro RPC and Protocols

Avro includes a full **RPC system** built on its binary encoding. This is less commonly used today (gRPC/HTTP2 dominate), but it is part of the spec and worth understanding.

### 13.1 Protocol Definition

A protocol is a named collection of messages (RPCs):

```json
{
  "protocol": "UserService",
  "namespace": "com.example",
  "types": [
    {
      "type": "record",
      "name": "User",
      "fields": [
        { "name": "id",   "type": "long" },
        { "name": "name", "type": "string" }
      ]
    },
    {
      "type": "error",
      "name": "UserNotFound",
      "fields": [
        { "name": "id",      "type": "long" },
        { "name": "message", "type": "string" }
      ]
    }
  ],
  "messages": {
    "getUser": {
      "request": [{ "name": "id", "type": "long" }],
      "response": "User",
      "errors": ["UserNotFound"],
      "one-way": false
    },
    "deleteUser": {
      "request": [{ "name": "id", "type": "long" }],
      "response": "null",
      "one-way": true
    }
  }
}
```

### 13.2 Avro RPC Handshake

Every Avro RPC session begins with a **handshake** to negotiate schemas between client and server:

```
Client → Server: HandshakeRequest
  clientHash    (MD5 of client protocol)
  clientProtocol (optional: full protocol JSON if server doesn't know it)
  serverHash    (MD5 of what client thinks server's protocol is)
  meta          (optional metadata map)

Server → Client: HandshakeResponse
  match:        "BOTH" | "CLIENT" | "NONE"
  serverProtocol (if match != "BOTH", server sends its protocol)
  serverHash    (MD5 of server protocol)
  meta
```

After handshake, requests and responses are serialized using the negotiated schemas.

### 13.3 Transport Layers

Avro RPC supports two transport types:

- **HTTP Transport**: Avro frames sent over HTTP/POST
- **Socket Transport**: Raw TCP with Avro framing

Avro framing: A sequence of `[4-byte big-endian length][bytes]` fragments, terminated by a zero-length fragment.

---

## 14. Schema Registry — Confluent and Beyond

In streaming systems (Kafka), schemas must be managed centrally. Every Kafka message must be paired with a schema, but you cannot embed the full schema in every message — that would destroy the compactness advantage.

### 14.1 The Schema Registry Pattern

```
┌──────────────────────────────────────────────────────────┐
│                  Schema Registry                         │
│                                                          │
│  subject: "orders-value"                                 │
│  versions:                                               │
│    id=1  → schema V1                                     │
│    id=2  → schema V2                                     │
│    id=3  → schema V3                                     │
└──────────────────────────────────────────────────────────┘
         ▲                    ▲
         │ register/lookup    │ lookup
         │                    │
   ┌─────────────┐    ┌──────────────┐
   │  Producer   │    │  Consumer    │
   │             │    │              │
   │ Serialize:  │    │ Deserialize: │
   │ [0][schema_id][avro_bytes]      │
   └─────────────┘    └──────────────┘
```

### 14.2 Confluent Wire Format

Every Avro-encoded Kafka message in the Confluent ecosystem uses this wire format:

```
Byte 0:   Magic byte = 0x00
Bytes 1-4: Schema ID (4-byte big-endian int)
Bytes 5+:  Avro binary-encoded payload
```

The schema ID is looked up in the Schema Registry to get the writer schema. The consumer's registered reader schema is used for resolution. **This 5-byte header is the only overhead per message** — all compactness of Avro binary is preserved.

### 14.3 Confluent Schema Registry API

The Schema Registry exposes a REST API:

```bash
# Register a schema
curl -X POST http://localhost:8081/subjects/orders-value/versions \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d '{"schema": "{\"type\":\"record\",\"name\":\"Order\",\"fields\":[...]}"}'

# Response: {"id": 1}

# Get schema by ID
curl http://localhost:8081/schemas/ids/1

# Get all versions of a subject
curl http://localhost:8081/subjects/orders-value/versions

# Get schema for a subject version
curl http://localhost:8081/subjects/orders-value/versions/1

# Check compatibility
curl -X POST http://localhost:8081/compatibility/subjects/orders-value/versions/latest \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d '{"schema": "..."}'

# Set compatibility mode for a subject
curl -X PUT http://localhost:8081/config/orders-value \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d '{"compatibility": "FULL"}'
```

### 14.4 Compatibility Modes in Schema Registry

| Mode | Description |
|---|---|
| `BACKWARD` | New schema readable by latest registered consumer |
| `BACKWARD_TRANSITIVE` | New schema readable by ALL registered consumers |
| `FORWARD` | Latest registered producer schema readable by new schema |
| `FORWARD_TRANSITIVE` | All registered producer schemas readable by new schema |
| `FULL` | BACKWARD + FORWARD |
| `FULL_TRANSITIVE` | BACKWARD_TRANSITIVE + FORWARD_TRANSITIVE |
| `NONE` | No compatibility checking |

**Recommendation**: Use `FULL_TRANSITIVE` for event sourcing and audit logs where you must be able to read any historical data with any version of the schema.

### 14.5 Subject Naming Strategies

| Strategy | Subject Name | Use Case |
|---|---|---|
| `TopicNameStrategy` | `{topic}-key` or `{topic}-value` | Default — one schema per topic |
| `RecordNameStrategy` | `{record_fullname}` | Multiple record types per topic |
| `TopicRecordNameStrategy` | `{topic}-{record_fullname}` | Multiple types + topic scoping |

---

## 15. Avro with Apache Kafka

### 15.1 Architecture Overview

```
Producer App
  │
  │ 1. Serialize: Schema → Schema Registry
  │             → Get/Register Schema ID
  │             → Avro encode
  │             → Prepend magic byte + schema ID
  ▼
Kafka Broker (Topic: orders)
  │
  │ Messages: [0x00][schema_id_4bytes][avro_payload]
  │
  ▼
Consumer App
  │ 1. Read magic byte (0x00) → Avro format confirmed
  │ 2. Read schema ID → fetch writer schema from registry
  │ 3. Load reader schema (application's current schema)
  │ 4. Avro decode with schema resolution
  ▼
  Deserialized Java/Go/Rust object
```

### 15.2 Kafka Producer with Avro (Configuration)

```properties
# kafka-producer.properties
bootstrap.servers=broker1:9092,broker2:9092
key.serializer=io.confluent.kafka.serializers.KafkaAvroSerializer
value.serializer=io.confluent.kafka.serializers.KafkaAvroSerializer
schema.registry.url=http://schema-registry:8081
auto.register.schemas=true
use.latest.version=false
```

### 15.3 Kafka Consumer with Avro (Configuration)

```properties
# kafka-consumer.properties
bootstrap.servers=broker1:9092,broker2:9092
key.deserializer=io.confluent.kafka.serializers.KafkaAvroDeserializer
value.deserializer=io.confluent.kafka.serializers.KafkaAvroDeserializer
schema.registry.url=http://schema-registry:8081
specific.avro.reader=true
group.id=my-consumer-group
auto.offset.reset=earliest
```

### 15.4 Schema Evolution in Kafka — Critical Scenario

**Scenario**: Topic `orders` has been receiving data for 6 months. Schema V1. You need to add a `discount` field.

**Safe evolution procedure**:

```bash
# 1. Check current compatibility mode
curl http://localhost:8081/config/orders-value
# → {"compatibility": "FULL"}

# 2. Design V2 schema with default
cat order_v2.avsc
{
  "type": "record",
  "name": "Order",
  "fields": [
    { "name": "id",       "type": "long" },
    { "name": "total",    "type": "double" },
    { "name": "discount", "type": ["null", "double"], "default": null }
  ]
}

# 3. Check compatibility before registering
curl -X POST http://localhost:8081/compatibility/subjects/orders-value/versions/latest \
  -d '{"schema": "...V2 JSON..."}'
# → {"is_compatible": true}

# 4. Register new version
curl -X POST http://localhost:8081/subjects/orders-value/versions \
  -d '{"schema": "...V2 JSON..."}'
# → {"id": 2}

# 5. Deploy consumers first (they can read both V1 and V2 — backward compat)
# 6. Deploy producers last (start producing V2)
```

**Deploy order for backward compatibility**: Consumers first, then Producers. This ensures consumers can always read the data being produced.

### 15.5 Kafka Streams with Avro

```properties
# kafka-streams.properties
application.id=order-processor
bootstrap.servers=broker:9092
default.key.serde=io.confluent.kafka.streams.serdes.avro.GenericAvroSerde
default.value.serde=io.confluent.kafka.streams.serdes.avro.GenericAvroSerde
schema.registry.url=http://schema-registry:8081
```

### 15.6 Multiple Event Types on One Topic

This is a common design pattern — using a union schema to put multiple event types on one topic:

```json
{
  "type": "record",
  "name": "Envelope",
  "namespace": "com.example",
  "fields": [
    {
      "name": "payload",
      "type": [
        "com.example.OrderCreated",
        "com.example.OrderUpdated",
        "com.example.OrderCancelled"
      ]
    },
    { "name": "event_time", "type": "long" },
    { "name": "source",     "type": "string" }
  ]
}
```

**Alternative**: Use `TopicRecordNameStrategy` and let consumers filter by message type.

### 15.7 Exactly-Once Semantics with Avro

Avro encoding is stateless and idempotent — the same data always produces the same bytes given the same schema. This is important for Kafka's exactly-once processing: schema ID + Avro bytes can be safely replayed. The schema registry ensures schema IDs are stable and never change their meaning.

---

## 16. Avro with Apache Hadoop

### 16.1 Hadoop and Avro — Why They're Paired

Avro was created specifically for Hadoop. Three properties make it ideal:

1. **Splittable OCF files**: Hadoop MapReduce splits files across multiple nodes. OCF's sync markers make this possible without central coordination.

2. **Schema in the file**: No external schema files needed on each TaskTracker. The schema travels with the data in the OCF header.

3. **Hadoop native libraries**: Avro ships with `AvroInputFormat`, `AvroOutputFormat`, `AvroMapper`, `AvroReducer` — first-class Hadoop citizens.

### 16.2 HDFS Storage Patterns

**Standard layout for Avro in HDFS**:

```
/data/
  warehouse/
    orders/
      year=2024/
        month=01/
          day=01/
            part-00000.avro   # 128MB target size (HDFS block size)
            part-00001.avro
        month=02/
          ...
```

**File sizing**: Target ~128 MB per Avro file (matching HDFS block size). Too many small files → NameNode pressure. Too large → poor parallelism.

### 16.3 Avro MapReduce Integration

```java
// MapReduce job configuration (Java reference)
Job job = Job.getInstance(conf, "Avro Word Count");

// Input: Avro files
AvroJob.setInputKeySchema(job, User.getClassSchema());
FileInputFormat.addInputPath(job, new Path("/data/users/*.avro"));
job.setInputFormatClass(AvroKeyInputFormat.class);

// Output: Avro files
AvroJob.setOutputKeySchema(job, wordCountSchema);
FileOutputFormat.setOutputPath(job, new Path("/output/wordcount"));
job.setOutputFormatClass(AvroKeyOutputFormat.class);
AvroJob.setOutputCodec(job, CodecFactory.snappyCodec());
```

### 16.4 Avro Merging — Combining Files in HDFS

```bash
# Using avro-tools to merge multiple Avro files
java -jar avro-tools.jar cat \
  /data/orders/2024-01-01/part-*.avro \
  /data/orders/2024-01-02/part-*.avro \
  --out /data/orders/merged/2024-01.avro

# Or use the fromjson / tojson for inspection
java -jar avro-tools.jar tojson /data/orders/part-00000.avro | head -20
```

### 16.5 Schema Management in HDFS

Store canonical schemas in HDFS alongside data:

```
/schemas/
  orders/
    current.avsc          → symlink or latest version
    v1.avsc
    v2.avsc
    v3.avsc
```

Alternatively, use a Schema Registry (even for batch Hadoop workflows) — it provides versioning, compatibility checking, and a single source of truth.

### 16.6 Avro and HDFS NameNode Considerations

Each HDFS file consumes **~150 bytes of NameNode heap** for metadata. A cluster with 100 million small Avro files needs ~15 GB of NameNode heap. Use **sequence files** or **merged Avro files** to keep the file count manageable.

**NameNode pressure formula**:
```
NameNode heap ≈ number_of_files × 150 bytes
                + number_of_blocks × 250 bytes
                + replication_factor × number_of_blocks × 100 bytes
```

---

## 17. Avro with Apache Spark

### 17.1 Spark-Avro Library

Spark has built-in Avro support via `spark-avro` (included in Spark 2.4+):

```python
# Python (PySpark) — reference only
spark.read.format("avro").load("/data/orders/*.avro")
df.write.format("avro").save("/output/orders")
```

For Go-based Spark interaction, use the Spark REST API or run PySpark jobs via subprocess.

### 17.2 Schema Evolution in Spark

Spark can handle Avro schema evolution when reading multiple files with different schemas:

```python
# Enable schema merging (union of all schemas)
spark.read.format("avro") \
  .option("mergeSchema", "true") \
  .load("/data/orders/year=*/")
```

With `mergeSchema=true`, Spark computes the union schema of all files and fills missing fields with `null`.

### 17.3 Avro Schema to Spark Schema Mapping

| Avro Type | Spark SQL Type |
|---|---|
| `null` | `NullType` |
| `boolean` | `BooleanType` |
| `int` | `IntegerType` |
| `long` | `LongType` |
| `float` | `FloatType` |
| `double` | `DoubleType` |
| `bytes` | `BinaryType` |
| `string` | `StringType` |
| `record` | `StructType` |
| `array` | `ArrayType` |
| `map` | `MapType(StringType, ...)` |
| `union` | `StructType` (nullable) or `StructType` with branches |
| `enum` | `StringType` |
| `fixed` | `BinaryType` |
| `date` | `DateType` |
| `timestamp-millis` | `TimestampType` |
| `timestamp-micros` | `TimestampType` |
| `decimal` | `DecimalType(precision, scale)` |

### 17.4 Avro vs Parquet in Spark

| Aspect | Avro | Parquet |
|---|---|---|
| Storage layout | Row-oriented | Column-oriented |
| Write speed | Fast | Slower (columnar encoding overhead) |
| Read all columns | Comparable | Comparable |
| Read few columns | Must read all columns | Only reads needed columns |
| Schema evolution | Native | Limited |
| Streaming writes | Excellent | Limited |
| Analytics (SELECT col FROM ...) | Poor | Excellent |

**Rule**: Use Avro for **write-heavy streaming** and inter-service data exchange. Use Parquet for **read-heavy analytics**. Many pipelines write Avro first, then compact to Parquet for analytics.

---

## 18. Avro with Apache Hive

### 18.1 Hive Avro SerDe

Hive uses a **SerDe** (Serializer/Deserializer) to read Avro files. The Avro SerDe is included in Hive and reads OCF files natively.

```sql
-- Create external Hive table over Avro files in HDFS
CREATE EXTERNAL TABLE orders (
  -- Hive infers columns from the Avro schema
  -- Do NOT define columns explicitly — let Avro SerDe do it
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.avro.AvroSerDe'
STORED AS INPUTFORMAT 'org.apache.hadoop.hive.ql.io.avro.AvroContainerInputFormat'
OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.avro.AvroContainerOutputFormat'
LOCATION 'hdfs:///data/orders/'
TBLPROPERTIES (
  'avro.schema.url'='hdfs:///schemas/orders/current.avsc'
);
```

### 18.2 Schema URL vs Inline Schema

**Option 1: Schema URL (recommended)**:
```sql
TBLPROPERTIES (
  'avro.schema.url'='hdfs:///schemas/orders/v3.avsc'
);
```

**Option 2: Inline schema literal**:
```sql
TBLPROPERTIES (
  'avro.schema.literal'='{"type":"record","name":"Order","fields":[...]}'
);
```

**Use schema URL** in production — it allows schema updates without `ALTER TABLE`. Change the file at the schema URL and Hive picks it up immediately (for new queries).

### 18.3 Hive Schema Evolution with Avro

When the Avro schema evolves, update the schema file at `avro.schema.url`. Hive will use the new schema to read new files and the reader schema to resolve differences with old files (via Avro's schema resolution).

```bash
# Update schema on HDFS
hadoop fs -put -f order_v4.avsc hdfs:///schemas/orders/current.avsc
```

### 18.4 Hive Partitioned Tables with Avro

```sql
CREATE EXTERNAL TABLE orders_partitioned (
)
PARTITIONED BY (year INT, month INT)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.avro.AvroSerDe'
STORED AS INPUTFORMAT 'org.apache.hadoop.hive.ql.io.avro.AvroContainerInputFormat'
OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.avro.AvroContainerOutputFormat'
LOCATION 'hdfs:///data/orders/'
TBLPROPERTIES (
  'avro.schema.url'='hdfs:///schemas/orders/current.avsc'
);

-- Add partitions manually
ALTER TABLE orders_partitioned
ADD PARTITION (year=2024, month=1)
LOCATION 'hdfs:///data/orders/year=2024/month=01/';

-- Or use MSCK REPAIR TABLE to discover partitions automatically
MSCK REPAIR TABLE orders_partitioned;
```

---

## 19. Avro with Apache Flink

### 19.1 Flink and Avro

Flink supports Avro for both batch and streaming with the `flink-avro` module.

```xml
<!-- Maven dependency -->
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-avro</artifactId>
  <version>1.18.0</version>
</dependency>

<!-- For Confluent Schema Registry integration -->
<dependency>
  <groupId>org.apache.flink</groupId>
  <artifactId>flink-avro-confluent-registry</artifactId>
  <version>1.18.0</version>
</dependency>
```

### 19.2 Avro in Flink Kafka Sources

```java
// Flink source with Avro deserialization (Java reference)
KafkaSource<Order> source = KafkaSource.<Order>builder()
  .setBootstrapServers("broker:9092")
  .setTopics("orders")
  .setGroupId("flink-processor")
  .setValueOnlyDeserializer(
    ConfluentRegistryAvroDeserializationSchema.forSpecific(
      Order.class,
      "http://schema-registry:8081"
    )
  )
  .build();
```

### 19.3 Watermarking and Event Time with Avro Timestamps

When using Avro's `timestamp-micros` logical type for event time, Flink can use it for watermarking:

```java
// Assign watermarks based on Avro timestamp field
WatermarkStrategy.<Order>forBoundedOutOfOrderness(Duration.ofSeconds(5))
  .withTimestampAssigner(
    (order, recordTimestamp) -> order.getEventTimeMicros() / 1000 // to millis
  );
```

---

## 20. Avro on Linux — CLI Tools and Ecosystem

### 20.1 Installing avro-tools

```bash
# Download avro-tools JAR (requires Java 8+)
wget https://repo1.maven.org/maven2/org/apache/avro/avro-tools/1.11.3/avro-tools-1.11.3.jar
mv avro-tools-1.11.3.jar /usr/local/lib/avro-tools.jar

# Create a convenient alias
echo 'alias avro-tools="java -jar /usr/local/lib/avro-tools.jar"' >> ~/.bashrc
source ~/.bashrc

# Verify
avro-tools --help
```

### 20.2 avro-tools Commands Reference

```bash
# Convert Avro binary to JSON (human-readable inspection)
avro-tools tojson data.avro

# Pretty-print JSON
avro-tools tojson data.avro | python3 -m json.tool | head -50

# Convert JSON to Avro binary
avro-tools fromjson --schema-file schema.avsc data.json > data.avro

# Print the schema embedded in an OCF file
avro-tools getschema data.avro

# Count records in an Avro file
avro-tools count data.avro

# Concatenate multiple Avro files (schemas must be compatible)
avro-tools cat file1.avro file2.avro --out merged.avro

# Compile Avro IDL to JSON schema
avro-tools idl schema.avdl schema.avsc

# Compile IDL to JSON schemata (one file per named type)
avro-tools idl2schemata schema.avdl output_dir/

# Generate Java code from schema (if using Java code generation)
avro-tools compile schema schema.avsc output_java_dir/

# Repair a corrupted Avro file (re-syncs blocks)
avro-tools recodec --codec snappy corrupted.avro repaired.avro
```

### 20.3 Inspecting Avro Files with Shell Tools

```bash
# View first 5 records as JSON
avro-tools tojson large_file.avro | head -n 5

# Count total records
avro-tools count large_file.avro

# Get schema and format it
avro-tools getschema large_file.avro | python3 -m json.tool

# Check file size and estimate compression
ls -lh large_file.avro
avro-tools count large_file.avro   # records
# Estimate: file_size / record_count = avg bytes per record

# Find schema ID (Confluent format) in a raw Kafka message dump
xxd message.bin | head -3
# Byte 0: 00 (magic)
# Bytes 1-4: schema_id in big-endian hex

# Extract schema ID from Confluent-encoded bytes
python3 -c "
import struct, sys
data = open('message.bin', 'rb').read()
assert data[0] == 0, 'Not Confluent Avro format'
schema_id = struct.unpack('>I', data[1:5])[0]
print(f'Schema ID: {schema_id}')
print(f'Payload bytes: {len(data) - 5}')
"
```

### 20.4 avro-python3 CLI (fastavro)

```bash
# Install fastavro (faster Python Avro library)
pip3 install fastavro

# Python script for quick inspection
python3 -c "
import fastavro, sys
with open(sys.argv[1], 'rb') as f:
    reader = fastavro.reader(f)
    print('Schema:', reader.writer_schema)
    for i, record in enumerate(reader):
        print(record)
        if i >= 4: break
" data.avro
```

### 20.5 Schema Registry CLI Tools

```bash
# Install schema-registry-cli (third-party tool)
pip3 install schema-registry-cli

# Or use kafkacat / kcat for testing
apt-get install kafkacat   # or: brew install kcat

# Consume Avro messages from Kafka with schema resolution
kcat -b broker:9092 -t orders -s value=avro -r http://schema-registry:8081 -C -c 10

# Produce a test Avro message
echo '{"id": 1, "name": "test"}' | \
  kcat -b broker:9092 -t test-topic -s value=avro -r http://schema-registry:8081 -P
```

### 20.6 Linux System Setup for Avro Development

```bash
# Install Java (required for avro-tools)
sudo apt-get update
sudo apt-get install -y openjdk-17-jdk

# Install Go (for Go Avro development)
wget https://go.dev/dl/go1.22.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.22.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin

# Install Rust (for Rust Avro development)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# Install Python Avro libraries
pip3 install fastavro avro-python3

# Install Kafka CLI tools
wget https://archive.apache.org/dist/kafka/3.6.0/kafka_2.13-3.6.0.tgz
tar -xzf kafka_2.13-3.6.0.tgz
export PATH=$PATH:$(pwd)/kafka_2.13-3.6.0/bin

# Start local Kafka with KRaft (no Zookeeper)
# (using Confluent Platform for Schema Registry)
wget https://packages.confluent.io/archive/7.6/confluent-7.6.0.tar.gz
tar -xzf confluent-7.6.0.tar.gz
cd confluent-7.6.0
bin/confluent local services start
```

### 20.7 Avro File Monitoring with Linux Tools

```bash
# Monitor Avro file growth
watch -n 1 'ls -lh /data/orders/*.avro'

# Watch Kafka consumer lag for Avro topics
kafka-consumer-groups.sh --bootstrap-server broker:9092 \
  --describe --group my-avro-consumer

# Check Schema Registry health
curl -s http://localhost:8081/subjects | python3 -m json.tool

# Monitor Schema Registry logs
tail -f /var/log/confluent/schema-registry/schema-registry.log | grep ERROR

# Process many Avro files in parallel with xargs
find /data/orders/ -name "*.avro" -print0 | \
  xargs -0 -P 8 -I {} sh -c 'avro-tools count {} >> /tmp/counts.txt'
```

---

## 21. Avro in Go — Idiomatic Implementation

### 21.1 Library: hamba/avro

The most complete and idiomatic Go Avro library is `github.com/hamba/avro/v2`.

```bash
go get github.com/hamba/avro/v2
go get github.com/hamba/avro/v2/ocf
```

### 21.2 Schema Parsing

```go
package main

import (
    "fmt"
    "log"

    "github.com/hamba/avro/v2"
)

func main() {
    // Parse schema from string
    schema, err := avro.Parse(`{
        "type": "record",
        "name": "User",
        "namespace": "com.example",
        "fields": [
            {"name": "id",       "type": "long"},
            {"name": "username", "type": "string"},
            {"name": "email",    "type": ["null", "string"], "default": null},
            {"name": "age",      "type": "int", "default": 0}
        ]
    }`)
    if err != nil {
        log.Fatalf("schema parse failed: %v", err)
    }
    fmt.Println("Schema type:", schema.Type())

    // Parse schema from file
    schemaBytes, _ := os.ReadFile("user.avsc")
    schema, err = avro.ParseBytes(schemaBytes)
}
```

### 21.3 Struct Mapping

```go
// Go struct — fields must match Avro field names (or use tags)
type User struct {
    ID       int64   `avro:"id"`
    Username string  `avro:"username"`
    Email    *string `avro:"email"`   // pointer = nullable (maps to ["null","string"])
    Age      int32   `avro:"age"`
}

// Encoding
schema, _ := avro.Parse(`...`)

user := User{
    ID:       42,
    Username: "alice",
    Email:    ptr("alice@example.com"), // helper: func ptr(s string) *string { return &s }
    Age:      30,
}

// Serialize to bytes
data, err := avro.Marshal(schema, user)
if err != nil {
    log.Fatal(err)
}

// Deserialize from bytes
var decoded User
err = avro.Unmarshal(schema, data, &decoded)
if err != nil {
    log.Fatal(err)
}
fmt.Printf("%+v\n", decoded)
```

### 21.4 Generic (Schema-Driven) API

When you don't have a compile-time struct, use the generic API:

```go
// avro.GenericRecord is a map-like structure
record := avro.NewGenericRecord(schema)

// Encoding a generic record
data, err := avro.Marshal(schema, record)

// Decoding to map
var result map[string]interface{}
err = avro.Unmarshal(schema, data, &result)
fmt.Println(result["username"])
```

### 21.5 OCF File Writing

```go
package main

import (
    "os"
    "log"

    "github.com/hamba/avro/v2"
    "github.com/hamba/avro/v2/ocf"
)

func main() {
    schema, _ := avro.Parse(`{
        "type": "record",
        "name": "Event",
        "fields": [
            {"name": "id",        "type": "long"},
            {"name": "event_type","type": "string"},
            {"name": "ts",        "type": {"type": "long", "logicalType": "timestamp-millis"}}
        ]
    }`)

    // Create output file
    f, err := os.Create("events.avro")
    if err != nil {
        log.Fatal(err)
    }
    defer f.Close()

    // Create OCF encoder with Snappy compression
    enc, err := ocf.NewEncoder(
        schema.String(),
        f,
        ocf.WithCodec(ocf.Snappy),
        ocf.WithBlockLength(1000), // records per block
    )
    if err != nil {
        log.Fatal(err)
    }

    type Event struct {
        ID        int64  `avro:"id"`
        EventType string `avro:"event_type"`
        Ts        int64  `avro:"ts"`
    }

    // Write records
    for i := int64(0); i < 10000; i++ {
        err = enc.Encode(Event{
            ID:        i,
            EventType: "click",
            Ts:        time.Now().UnixMilli(),
        })
        if err != nil {
            log.Fatal(err)
        }
    }

    // Flush must be called — data may be buffered in blocks
    if err = enc.Flush(); err != nil {
        log.Fatal(err)
    }
}
```

### 21.6 OCF File Reading

```go
func readOCF(filename string) error {
    f, err := os.Open(filename)
    if err != nil {
        return err
    }
    defer f.Close()

    dec, err := ocf.NewDecoder(f)
    if err != nil {
        return err
    }

    type Event struct {
        ID        int64  `avro:"id"`
        EventType string `avro:"event_type"`
        Ts        int64  `avro:"ts"`
    }

    count := 0
    for dec.HasNext() {
        var evt Event
        if err := dec.Decode(&evt); err != nil {
            return fmt.Errorf("decode error: %w", err)
        }
        count++
        _ = evt
    }

    if err := dec.Error(); err != nil {
        return fmt.Errorf("reader error: %w", err)
    }

    fmt.Printf("Read %d records\n", count)
    return nil
}
```

### 21.7 Schema Resolution in Go

```go
// Reader schema (new version with extra field)
readerSchemaJSON := `{
    "type": "record",
    "name": "User",
    "fields": [
        {"name": "id",       "type": "long"},
        {"name": "username", "type": "string"},
        {"name": "email",    "type": ["null", "string"], "default": null},
        {"name": "tier",     "type": "string", "default": "free"}  // NEW field
    ]
}`

// Writer schema (old version, no 'tier' field)
writerSchemaJSON := `{
    "type": "record",
    "name": "User",
    "fields": [
        {"name": "id",       "type": "long"},
        {"name": "username", "type": "string"},
        {"name": "email",    "type": ["null", "string"], "default": null}
    ]
}`

writerSchema, _ := avro.Parse(writerSchemaJSON)
readerSchema, _ := avro.Parse(readerSchemaJSON)

// Create a compatible (resolving) schema
compatible, err := avro.NewSchemaCompatibility().Compatible(
    readerSchema, writerSchema,
)
if err != nil {
    log.Fatalf("schemas incompatible: %v", err)
}

// Decode with schema resolution
type UserV2 struct {
    ID       int64   `avro:"id"`
    Username string  `avro:"username"`
    Email    *string `avro:"email"`
    Tier     string  `avro:"tier"` // will be "free" for old records
}

var user UserV2
err = avro.UnmarshalWithSchema(compatible, data, &user)
```

### 21.8 Kafka Integration in Go

```go
package main

import (
    "context"
    "encoding/binary"
    "fmt"
    "log"

    "github.com/hamba/avro/v2"
    "github.com/segmentio/kafka-go"
)

const (
    MagicByte = 0x00
)

// ConfluentEncoder encodes an Avro value with Confluent wire format
func ConfluentEncode(schemaID int32, schema avro.Schema, value interface{}) ([]byte, error) {
    // Serialize the Avro value
    payload, err := avro.Marshal(schema, value)
    if err != nil {
        return nil, fmt.Errorf("avro marshal: %w", err)
    }

    // Prepend Confluent header: [0x00][4-byte big-endian schema ID]
    buf := make([]byte, 5+len(payload))
    buf[0] = MagicByte
    binary.BigEndian.PutUint32(buf[1:5], uint32(schemaID))
    copy(buf[5:], payload)
    return buf, nil
}

// ConfluentDecode decodes a Confluent wire format message
func ConfluentDecode(data []byte, schema avro.Schema, dest interface{}) (int32, error) {
    if len(data) < 5 {
        return 0, fmt.Errorf("message too short: %d bytes", len(data))
    }
    if data[0] != MagicByte {
        return 0, fmt.Errorf("invalid magic byte: %x", data[0])
    }

    schemaID := int32(binary.BigEndian.Uint32(data[1:5]))
    payload := data[5:]

    if err := avro.Unmarshal(schema, payload, dest); err != nil {
        return 0, fmt.Errorf("avro unmarshal: %w", err)
    }
    return schemaID, nil
}

type Order struct {
    ID    int64   `avro:"id"`
    Total float64 `avro:"total"`
    Item  string  `avro:"item"`
}

func main() {
    schema, _ := avro.Parse(`{
        "type": "record",
        "name": "Order",
        "fields": [
            {"name": "id",    "type": "long"},
            {"name": "total", "type": "double"},
            {"name": "item",  "type": "string"}
        ]
    }`)

    // Producer
    writer := &kafka.Writer{
        Addr:     kafka.TCP("localhost:9092"),
        Topic:    "orders",
        Balancer: &kafka.LeastBytes{},
    }
    defer writer.Close()

    order := Order{ID: 1001, Total: 29.99, Item: "book"}
    encoded, err := ConfluentEncode(1, schema, order)
    if err != nil {
        log.Fatal(err)
    }

    err = writer.WriteMessages(context.Background(),
        kafka.Message{
            Key:   []byte("order-1001"),
            Value: encoded,
        },
    )
    if err != nil {
        log.Fatal(err)
    }

    fmt.Printf("Produced order %d (%d bytes)\n", order.ID, len(encoded))
}
```

### 21.9 Performance Benchmarking in Go

```go
package main

import (
    "testing"
    "github.com/hamba/avro/v2"
)

var schema avro.Schema
var testUser = User{ID: 42, Username: "alice", Age: 30}

func init() {
    schema, _ = avro.Parse(`...`)
}

func BenchmarkAvroMarshal(b *testing.B) {
    b.ReportAllocs()
    for i := 0; i < b.N; i++ {
        _, err := avro.Marshal(schema, testUser)
        if err != nil {
            b.Fatal(err)
        }
    }
}

func BenchmarkAvroUnmarshal(b *testing.B) {
    data, _ := avro.Marshal(schema, testUser)
    b.ReportAllocs()
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        var u User
        if err := avro.Unmarshal(schema, data, &u); err != nil {
            b.Fatal(err)
        }
    }
}

// Run: go test -bench=. -benchmem -count=5 -benchtime=5s
```

---

## 22. Avro in Rust — Zero-Cost Abstractions

### 22.1 Library: apache-avro

```toml
# Cargo.toml
[dependencies]
apache-avro = { version = "0.16", features = ["snappy", "zstandard"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

### 22.2 Schema Parsing and Struct Serialization

```rust
use apache_avro::{Schema, Writer, Reader, from_value, to_value};
use serde::{Deserialize, Serialize};
use std::str::FromStr;

#[derive(Debug, Serialize, Deserialize, PartialEq)]
struct User {
    id: i64,
    username: String,
    email: Option<String>,     // Option<T> maps to ["null", "T"]
    age: i32,
}

fn main() -> Result<(), apache_avro::Error> {
    let schema_str = r#"{
        "type": "record",
        "name": "User",
        "namespace": "com.example",
        "fields": [
            {"name": "id",       "type": "long"},
            {"name": "username", "type": "string"},
            {"name": "email",    "type": ["null", "string"], "default": null},
            {"name": "age",      "type": "int", "default": 0}
        ]
    }"#;

    let schema = Schema::parse_str(schema_str)?;

    let user = User {
        id: 42,
        username: "alice".to_string(),
        email: Some("alice@example.com".to_string()),
        age: 30,
    };

    // Serialize to Avro bytes (raw, no OCF header)
    let mut writer = Writer::new(&schema, Vec::new());
    writer.append_ser(user)?;
    let encoded = writer.into_inner()?;

    println!("Encoded {} bytes", encoded.len());

    // Deserialize from bytes
    let reader = Reader::new(&encoded[..])?;
    for value in reader {
        let decoded_user: User = from_value(&value?)?;
        println!("{:?}", decoded_user);
    }

    Ok(())
}
```

### 22.3 OCF File Writing with Compression

```rust
use apache_avro::{Codec, Schema, Writer};
use serde::Serialize;
use std::fs::File;
use std::io::BufWriter;

fn write_ocf<T: Serialize>(
    schema: &Schema,
    records: &[T],
    path: &str,
    codec: Codec,
) -> Result<(), Box<dyn std::error::Error>> {
    let file = File::create(path)?;
    let buf_writer = BufWriter::new(file);

    let mut writer = Writer::builder()
        .schema(schema)
        .writer(buf_writer)
        .codec(codec)
        .block_size(10_000)  // records per block
        .build();

    for record in records {
        writer.append_ser(record)?;
    }

    writer.flush()?;
    println!("Wrote {} records to {}", records.len(), path);
    Ok(())
}
```

### 22.4 OCF File Reading

```rust
use apache_avro::{Reader, from_value};
use serde::Deserialize;
use std::fs::File;
use std::io::BufReader;

fn read_ocf<T: for<'de> Deserialize<'de> + std::fmt::Debug>(
    path: &str,
) -> Result<Vec<T>, Box<dyn std::error::Error>> {
    let file = File::open(path)?;
    let buf_reader = BufReader::new(file);

    let reader = Reader::new(buf_reader)?;
    let mut records = Vec::new();

    for result in reader {
        let value = result?;
        let record: T = from_value(&value)?;
        records.push(record);
    }

    Ok(records)
}
```

### 22.5 Schema Evolution in Rust

```rust
use apache_avro::{Schema, Reader};

fn read_with_evolution(
    data: &[u8],
    writer_schema_str: &str,
    reader_schema_str: &str,
) -> Result<Vec<apache_avro::types::Value>, apache_avro::Error> {
    let writer_schema = Schema::parse_str(writer_schema_str)?;
    let reader_schema = Schema::parse_str(reader_schema_str)?;

    // Reader with both schemas — applies resolution rules
    let reader = Reader::with_schema(&reader_schema, data)?;

    let mut values = Vec::new();
    for result in reader {
        values.push(result?);
    }
    Ok(values)
}
```

### 22.6 Confluent Wire Format in Rust

```rust
use apache_avro::{Schema, from_value};
use bytes::{Bytes, Buf};

const MAGIC_BYTE: u8 = 0x00;

#[derive(Debug)]
struct ConfluentMessage {
    schema_id: u32,
    payload: Vec<u8>,
}

fn decode_confluent(raw: &[u8]) -> Result<ConfluentMessage, Box<dyn std::error::Error>> {
    if raw.len() < 5 {
        return Err("Message too short".into());
    }
    if raw[0] != MAGIC_BYTE {
        return Err(format!("Invalid magic byte: 0x{:02x}", raw[0]).into());
    }

    let schema_id = u32::from_be_bytes([raw[1], raw[2], raw[3], raw[4]]);
    let payload = raw[5..].to_vec();

    Ok(ConfluentMessage { schema_id, payload })
}

fn encode_confluent(schema_id: u32, avro_bytes: Vec<u8>) -> Vec<u8> {
    let mut buf = Vec::with_capacity(5 + avro_bytes.len());
    buf.push(MAGIC_BYTE);
    buf.extend_from_slice(&schema_id.to_be_bytes());
    buf.extend(avro_bytes);
    buf
}
```

### 22.7 Performance: Rust Avro Patterns

```rust
// Pre-parse schemas at startup, not in hot paths
use std::sync::OnceLock;

static SCHEMA: OnceLock<Schema> = OnceLock::new();

fn get_schema() -> &'static Schema {
    SCHEMA.get_or_init(|| {
        Schema::parse_str(include_str!("../schemas/user.avsc"))
            .expect("Invalid schema")
    })
}

// Reuse Writer buffers to avoid allocations
fn batch_encode(records: &[User]) -> Result<Vec<Vec<u8>>, apache_avro::Error> {
    let schema = get_schema();
    let mut results = Vec::with_capacity(records.len());

    for record in records {
        let mut writer = Writer::new(schema, Vec::with_capacity(256));
        writer.append_ser(record)?;
        results.push(writer.into_inner()?);
    }
    Ok(results)
}
```

---

## 23. Avro in Python — Reference Implementation

### 23.1 Library Options

| Library | Speed | Features | Recommendation |
|---|---|---|---|
| `avro-python3` | Slow (pure Python) | Full spec compliance | Testing/reference |
| `fastavro` | Fast (Cython) | Most features | Production |

```bash
pip3 install fastavro
```

### 23.2 fastavro — Core Usage

```python
import fastavro
from fastavro import writer, reader, parse_schema
import io

# Parse schema
schema = parse_schema({
    "type": "record",
    "name": "User",
    "namespace": "com.example",
    "fields": [
        {"name": "id",       "type": "long"},
        {"name": "username", "type": "string"},
        {"name": "email",    "type": ["null", "string"], "default": None},
        {"name": "age",      "type": "int", "default": 0},
    ]
})

# Write to buffer (OCF format)
records = [
    {"id": 1, "username": "alice", "email": "alice@example.com", "age": 30},
    {"id": 2, "username": "bob",   "email": None, "age": 25},
]

buf = io.BytesIO()
fastavro.writer(buf, schema, records, codec='snappy')
buf.seek(0)

# Read back
for record in fastavro.reader(buf):
    print(record)

# Write to file
with open("users.avro", "wb") as f:
    fastavro.writer(f, schema, records, codec='zstandard')

# Read from file
with open("users.avro", "rb") as f:
    for record in fastavro.reader(f):
        print(record)
```

### 23.3 Schema Resolution in Python

```python
import fastavro

writer_schema = fastavro.parse_schema({
    "type": "record",
    "name": "User",
    "fields": [
        {"name": "id",       "type": "long"},
        {"name": "username", "type": "string"},
    ]
})

reader_schema = fastavro.parse_schema({
    "type": "record",
    "name": "User",
    "fields": [
        {"name": "id",       "type": "long"},
        {"name": "username", "type": "string"},
        {"name": "tier",     "type": "string", "default": "free"},  # new field
    ]
})

with open("old_data.avro", "rb") as f:
    # Pass reader_schema to apply resolution
    for record in fastavro.reader(f, reader_schema=reader_schema):
        print(record)  # tier will be "free" for old records
```

### 23.4 Raw Binary Encoding (No OCF)

```python
import fastavro
import io

schema = fastavro.parse_schema({"type": "record", "name": "Msg", "fields": [
    {"name": "id", "type": "long"},
    {"name": "body", "type": "string"}
]})

# Encode single record without OCF container
buf = io.BytesIO()
fastavro.schemaless_writer(buf, schema, {"id": 1, "body": "hello"})
raw_bytes = buf.getvalue()
print(f"Raw bytes: {raw_bytes.hex()}")

# Decode single record without OCF container
buf = io.BytesIO(raw_bytes)
record = fastavro.schemaless_reader(buf, schema)
print(record)
```

### 23.5 Confluent Wire Format in Python

```python
import struct
import io
import fastavro
import requests

MAGIC_BYTE = b'\x00'

def confluent_encode(schema_id: int, schema, record: dict) -> bytes:
    """Encode record with Confluent wire format header."""
    buf = io.BytesIO()
    fastavro.schemaless_writer(buf, schema, record)
    avro_bytes = buf.getvalue()
    return MAGIC_BYTE + struct.pack('>I', schema_id) + avro_bytes

def confluent_decode(data: bytes, schema_registry_url: str, read_schema) -> dict:
    """Decode a Confluent wire format message."""
    assert data[0:1] == MAGIC_BYTE, f"Invalid magic byte: {data[0]:02x}"
    schema_id = struct.unpack('>I', data[1:5])[0]
    payload = data[5:]

    # Optionally fetch writer schema from registry
    # writer_schema_json = requests.get(
    #     f"{schema_registry_url}/schemas/ids/{schema_id}"
    # ).json()['schema']

    buf = io.BytesIO(payload)
    return fastavro.schemaless_reader(buf, read_schema)
```

---

## 24. Avro in C — Low-Level Implementation

### 24.1 libavro-c

Apache Avro ships an official C library.

```bash
# Install on Ubuntu/Debian
sudo apt-get install -y libavro-dev

# Or build from source
git clone https://github.com/apache/avro
cd avro/lang/c
mkdir build && cd build
cmake ..
make -j$(nproc)
sudo make install
```

### 24.2 Writing Avro in C

```c
#include <avro.h>
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    avro_schema_t schema;
    avro_schema_error_t error;

    // Parse schema from JSON string
    const char *schema_json =
        "{"
        "  \"type\": \"record\","
        "  \"name\": \"User\","
        "  \"fields\": ["
        "    {\"name\": \"id\",       \"type\": \"long\"},"
        "    {\"name\": \"username\", \"type\": \"string\"}"
        "  ]"
        "}";

    if (avro_schema_from_json(schema_json, 0, &schema, &error)) {
        fprintf(stderr, "Schema parse error: %s\n", avro_strerror());
        return EXIT_FAILURE;
    }

    // Create a datum (record)
    avro_datum_t user_datum = avro_record(schema);

    avro_datum_t id_datum = avro_int64(42);
    avro_datum_t name_datum = avro_string("alice");

    avro_record_set(user_datum, "id", id_datum);
    avro_record_set(user_datum, "username", name_datum);

    // Write to OCF file
    avro_file_writer_t writer;
    if (avro_file_writer_create("users.avro", schema, &writer)) {
        fprintf(stderr, "File writer error: %s\n", avro_strerror());
        return EXIT_FAILURE;
    }

    if (avro_file_writer_append(writer, user_datum)) {
        fprintf(stderr, "Write error: %s\n", avro_strerror());
        return EXIT_FAILURE;
    }

    avro_file_writer_close(writer);

    // Cleanup
    avro_datum_decref(id_datum);
    avro_datum_decref(name_datum);
    avro_datum_decref(user_datum);
    avro_schema_decref(schema);

    printf("Wrote user to users.avro\n");
    return EXIT_SUCCESS;
}
```

### 24.3 Reading Avro in C

```c
#include <avro.h>
#include <stdio.h>

int main(void) {
    avro_file_reader_t reader;

    if (avro_file_reader("users.avro", &reader)) {
        fprintf(stderr, "Open error: %s\n", avro_strerror());
        return 1;
    }

    avro_schema_t schema = avro_file_reader_get_writer_schema(reader);
    avro_datum_t datum;
    int rval;

    while ((rval = avro_file_reader_read(reader, NULL, &datum)) == 0) {
        avro_datum_t id_field, name_field;
        avro_record_get(datum, "id", &id_field);
        avro_record_get(datum, "username", &name_field);

        int64_t id;
        char *name;
        avro_int64_get(id_field, &id);
        avro_string_get(name_field, &name);

        printf("User: id=%ld, username=%s\n", id, name);

        avro_datum_decref(datum);
    }

    avro_file_reader_close(reader);
    return 0;
}
```

### 24.4 Compiling C Avro Programs

```bash
gcc -o avro_writer avro_writer.c $(pkg-config --cflags --libs avro-1.0)
gcc -o avro_reader avro_reader.c -lavro
```

---

## 25. Performance Analysis and Benchmarking

### 25.1 Serialization Size Comparison

For a typical record `{id: 42, name: "Alice", active: true, score: 98.5}`:

| Format | Approximate Size |
|---|---|
| JSON | 58 bytes |
| XML | 95 bytes |
| Avro binary | 15 bytes |
| Protobuf | 16 bytes |
| MessagePack | 28 bytes |

**Avro size breakdown**:
```
id=42:     zigzag(42)=84 → 1 byte
name:      varint(5)=10 + "Alice"(5) = 6 bytes
active:    1 byte (boolean)
score:     8 bytes (double)
Total:     16 bytes (including all field data, no field names)
```

### 25.2 Throughput Benchmarks (Approximate)

| Language | Library | Serialize | Deserialize |
|---|---|---|---|
| Rust | apache-avro | ~500 MB/s | ~450 MB/s |
| Go | hamba/avro | ~350 MB/s | ~300 MB/s |
| C | libavro-c | ~400 MB/s | ~350 MB/s |
| Python | fastavro | ~80 MB/s | ~70 MB/s |
| Python | avro-python3 | ~5 MB/s | ~5 MB/s |

*Throughput varies by record complexity, field count, and hardware.*

### 25.3 Schema Parsing Cost

Schema parsing is **expensive**. Parse schemas once at startup and reuse the parsed schema object.

```go
// BAD: parse schema on every request
func handleRequest(data []byte) {
    schema, _ := avro.Parse(`...`) // expensive!
    avro.Unmarshal(schema, data, &obj)
}

// GOOD: parse schema once
var schema = func() avro.Schema {
    s, err := avro.Parse(`...`)
    if err != nil { panic(err) }
    return s
}()

func handleRequest(data []byte) {
    avro.Unmarshal(schema, data, &obj)
}
```

### 25.4 Memory Allocation Patterns

In Go, `avro.Marshal` always allocates a new `[]byte`. For high-throughput scenarios:

```go
// Use a sync.Pool for the encoder buffer
var bufPool = sync.Pool{
    New: func() interface{} { return make([]byte, 0, 512) },
}

// Note: hamba/avro does not currently support encoding into an existing buffer
// This is a known limitation; consider pre-allocating slices and managing pools
// at the application level (e.g., pool of *bytes.Buffer)
```

In Rust, the `apache-avro` Writer takes ownership of the output buffer — pre-allocate with capacity:

```rust
let mut writer = Writer::new(&schema, Vec::with_capacity(512));
```

---

## 26. Compression Codecs

### 26.1 Codec Selection Guide

| Codec | Compression Ratio | Speed | CPU Usage | Use Case |
|---|---|---|---|---|
| `null` | 1.0x (none) | Max | None | Already compressed data, debugging |
| `deflate` | 3-5x | Medium | Medium | General purpose, maximum compatibility |
| `snappy` | 2-3x | Very fast | Low | High-throughput streaming |
| `bzip2` | 4-7x | Slow | High | Cold storage, maximum space savings |
| `zstandard` | 3-6x | Fast | Low-Medium | Best general-purpose for production |
| `lz4` | 2-3x | Fastest | Very low | Real-time streaming, latency-sensitive |
| `xz` | 5-8x | Very slow | Very high | Archive storage |

### 26.2 Codec Configuration

In OCF headers:
```
avro.codec → "null" | "deflate" | "snappy" | "bzip2" | "zstandard" | "lz4" | "xz"
```

In Go:
```go
ocf.WithCodec(ocf.Snappy)
ocf.WithCodec(ocf.ZStandard)
ocf.WithCodec(ocf.Deflate)
```

In Python (fastavro):
```python
fastavro.writer(f, schema, records, codec='snappy')
fastavro.writer(f, schema, records, codec='zstandard')
fastavro.writer(f, schema, records, codec='deflate')
```

### 26.3 Compression vs Block Size Trade-off

Larger blocks compress better (more context for the algorithm) but:
- Require more memory to decompress
- Increase time-to-first-byte for streaming readers
- Reduce seek granularity for random access

**Optimal block configuration**:
```
For streaming (Kafka, real-time): 500–2,000 records/block
For HDFS batch: 10,000–50,000 records/block (~64MB uncompressed)
```

---

## 27. Security — Encryption and Authentication

### 27.1 Schema Registry Authentication

The Confluent Schema Registry supports:

```properties
# Basic Auth
schema.registry.basic.auth.credentials.source=USER_INFO
schema.registry.basic.auth.user.info=user:password

# SSL/TLS
schema.registry.ssl.truststore.location=/etc/kafka/ssl/schema-registry.truststore.jks
schema.registry.ssl.truststore.password=changeit
schema.registry.ssl.keystore.location=/etc/kafka/ssl/schema-registry.keystore.jks
schema.registry.ssl.keystore.password=changeit
schema.registry.ssl.key.password=changeit
```

### 27.2 Encrypting Field Values

Avro does not provide built-in field-level encryption, but you can layer it:

```python
from cryptography.fernet import Fernet
import fastavro
import io

key = Fernet.generate_key()
fernet = Fernet(key)

def encrypt_field(value: str) -> bytes:
    return fernet.encrypt(value.encode())

def decrypt_field(ciphertext: bytes) -> str:
    return fernet.decrypt(ciphertext).decode()

# Schema with encrypted fields stored as bytes
schema = fastavro.parse_schema({
    "type": "record",
    "name": "SecureUser",
    "fields": [
        {"name": "id",             "type": "long"},
        {"name": "encrypted_ssn",  "type": "bytes"},  # encrypted PII
        {"name": "username",       "type": "string"},  # plaintext
    ]
})

record = {
    "id": 42,
    "encrypted_ssn": encrypt_field("123-45-6789"),
    "username": "alice"
}

buf = io.BytesIO()
fastavro.schemaless_writer(buf, schema, record)
```

### 27.3 Access Control for Schema Registry

Use Confluent RBAC (Role-Based Access Control) to control who can:
- `READ`: Read schemas
- `WRITE`: Register new schemas
- `DELETE`: Delete subjects/versions
- `OWNER`: Full control

```bash
# Grant read access to consumer service account
confluent iam rbac role-binding create \
  --principal User:consumer-sa \
  --role ResourceOwner \
  --resource "Subject:orders-value" \
  --kafka-cluster-id <cluster-id> \
  --schema-registry-cluster-id <sr-cluster-id>
```

---

## 28. Advanced Schema Patterns

### 28.1 Recursive Schemas

Avro supports recursive types — a record that references itself:

```json
{
  "type": "record",
  "name": "TreeNode",
  "namespace": "com.example",
  "fields": [
    { "name": "value",    "type": "string" },
    {
      "name": "children",
      "type": {
        "type": "array",
        "items": "com.example.TreeNode"
      },
      "default": []
    }
  ]
}
```

**Caution**: Recursive schemas can produce infinitely deep data. Always bound recursion with `["null", "RecordType"]` unions at the recursive reference:

```json
{
  "name": "left",
  "type": ["null", "com.example.TreeNode"],
  "default": null
}
```

### 28.2 Polymorphism with Unions

Model inheritance/polymorphism using unions of named records:

```json
{
  "type": "record",
  "name": "Event",
  "namespace": "com.example",
  "fields": [
    { "name": "event_id",   "type": "string" },
    { "name": "timestamp",  "type": { "type": "long", "logicalType": "timestamp-millis" } },
    {
      "name": "payload",
      "type": [
        {
          "type": "record",
          "name": "UserCreated",
          "fields": [
            { "name": "user_id",  "type": "string" },
            { "name": "username", "type": "string" }
          ]
        },
        {
          "type": "record",
          "name": "OrderPlaced",
          "fields": [
            { "name": "order_id", "type": "string" },
            { "name": "total",    "type": "double" }
          ]
        },
        {
          "type": "record",
          "name": "PaymentReceived",
          "fields": [
            { "name": "payment_id", "type": "string" },
            { "name": "amount",     "type": "double" }
          ]
        }
      ]
    }
  ]
}
```

### 28.3 Envelope Pattern for Multi-Type Topics

```json
{
  "type": "record",
  "name": "Envelope",
  "namespace": "com.example",
  "fields": [
    { "name": "id",        "type": "string" },
    { "name": "source",    "type": "string" },
    { "name": "ts",        "type": { "type": "long", "logicalType": "timestamp-micros" } },
    { "name": "schema_version", "type": "int" },
    {
      "name": "data",
      "type": "bytes",
      "doc": "Avro-encoded payload. Type determined by 'source' field."
    },
    {
      "name": "metadata",
      "type": { "type": "map", "values": "string" },
      "default": {}
    }
  ]
}
```

### 28.4 Schema Design for Partitioned Kafka Topics

When designing Avro schemas for Kafka, always include the partition key fields in the value schema (even if they're also the key):

```json
{
  "type": "record",
  "name": "OrderEvent",
  "fields": [
    { "name": "tenant_id",  "type": "string" },  // used as Kafka key
    { "name": "order_id",   "type": "string" },
    { "name": "event_type", "type": "string" },
    { "name": "ts",         "type": { "type": "long", "logicalType": "timestamp-millis" } },
    { "name": "payload",    "type": { "type": "map", "values": "string" }, "default": {} }
  ]
}
```

This ensures event consumers who don't have access to the Kafka key metadata can still route by tenant.

### 28.5 Versioned Schema Pattern

Embed version metadata directly in the record:

```json
{
  "type": "record",
  "name": "VersionedRecord",
  "fields": [
    { "name": "_schema_version", "type": "int",    "default": 3 },
    { "name": "_schema_name",    "type": "string", "default": "com.example.User" },
    ...actual fields...
  ]
}
```

### 28.6 Nullable Fields — Comprehensive Patterns

```json
// Pattern 1: Simple nullable string
{ "name": "phone", "type": ["null", "string"], "default": null }

// Pattern 2: Nullable complex type
{ "name": "address", "type": ["null", {
    "type": "record",
    "name": "Address",
    "fields": [
        {"name": "street", "type": "string"},
        {"name": "city",   "type": "string"}
    ]
}], "default": null }

// Pattern 3: Optional with non-null default
{ "name": "tier", "type": ["string", "null"], "default": "free" }
// NOTE: when "string" is first, default must be a string, not null
```

---

## 29. Testing Avro Schemas and Data

### 29.1 Schema Compatibility Testing

```bash
# Test backward compatibility before deploying
curl -X POST \
  http://localhost:8081/compatibility/subjects/orders-value/versions/latest \
  -H "Content-Type: application/vnd.schemaregistry.v1+json" \
  -d "{\"schema\": $(cat new_order.avsc | jq -Rs .)}"
```

### 29.2 Unit Testing Schema Evolution in Go

```go
package avro_test

import (
    "testing"
    "github.com/hamba/avro/v2"
)

func TestBackwardCompatibility(t *testing.T) {
    writerSchemaJSON := `{
        "type": "record", "name": "User",
        "fields": [
            {"name": "id",   "type": "long"},
            {"name": "name", "type": "string"}
        ]
    }`
    readerSchemaJSON := `{
        "type": "record", "name": "User",
        "fields": [
            {"name": "id",    "type": "long"},
            {"name": "name",  "type": "string"},
            {"name": "email", "type": ["null","string"], "default": null}
        ]
    }`

    writerSchema, _ := avro.Parse(writerSchemaJSON)
    readerSchema, _ := avro.Parse(readerSchemaJSON)

    // Serialize with writer schema
    type UserV1 struct {
        ID   int64  `avro:"id"`
        Name string `avro:"name"`
    }
    data, err := avro.Marshal(writerSchema, UserV1{ID: 1, Name: "Alice"})
    if err != nil {
        t.Fatalf("marshal: %v", err)
    }

    // Deserialize with reader schema (schema resolution)
    type UserV2 struct {
        ID    int64   `avro:"id"`
        Name  string  `avro:"name"`
        Email *string `avro:"email"`
    }

    compat, err := avro.NewSchemaCompatibility().Compatible(readerSchema, writerSchema)
    if err != nil {
        t.Fatalf("schemas incompatible: %v", err)
    }

    var user UserV2
    if err := avro.UnmarshalWithSchema(compat, data, &user); err != nil {
        t.Fatalf("unmarshal: %v", err)
    }

    if user.ID != 1 || user.Name != "Alice" || user.Email != nil {
        t.Errorf("unexpected user: %+v", user)
    }
}
```

### 29.3 Property-Based Testing for Avro

Property: "serialization followed by deserialization is identity."

```go
import "testing/quick"

func TestAvroRoundTrip(t *testing.T) {
    schema, _ := avro.Parse(`...`)

    err := quick.Check(func(id int64, name string) bool {
        original := User{ID: id, Name: name}
        data, err := avro.Marshal(schema, original)
        if err != nil {
            return false
        }
        var decoded User
        if err := avro.Unmarshal(schema, data, &decoded); err != nil {
            return false
        }
        return original == decoded
    }, nil)

    if err != nil {
        t.Error(err)
    }
}
```

### 29.4 Validating Avro Files in CI/CD

```bash
#!/bin/bash
# validate_avro.sh — run in CI to check all schema files

set -euo pipefail

SCHEMA_DIR="schemas/"
AVRO_TOOLS="java -jar /usr/local/lib/avro-tools.jar"

echo "Validating Avro schemas..."
for schema_file in "$SCHEMA_DIR"/*.avsc; do
    echo -n "  Checking $schema_file... "
    # Try to parse the schema — exits non-zero if invalid
    $AVRO_TOOLS compile schema "$schema_file" /tmp/avro_compile_test/ 2>/dev/null \
        && echo "OK" || { echo "FAILED"; exit 1; }
done

echo "Checking schema compatibility..."
# Use Schema Registry API to check compatibility
for schema_file in schemas/new/*.avsc; do
    subject=$(basename "$schema_file" .avsc)-value
    echo -n "  Checking $subject... "
    result=$(curl -s -o /tmp/compat_result.json -w "%{http_code}" \
        -X POST \
        "http://schema-registry:8081/compatibility/subjects/$subject/versions/latest" \
        -H "Content-Type: application/vnd.schemaregistry.v1+json" \
        -d "{\"schema\": $(cat "$schema_file" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')}")
    if [ "$result" = "200" ] && grep -q '"is_compatible":true' /tmp/compat_result.json; then
        echo "Compatible"
    else
        echo "INCOMPATIBLE!"
        cat /tmp/compat_result.json
        exit 1
    fi
done

echo "All schemas valid and compatible."
```

---

## 30. Common Pitfalls and Anti-Patterns

### 30.1 Pitfall: Default Value Type Mismatch

```json
// WRONG: default null but string is first in union
{
  "name": "email",
  "type": ["string", "null"],
  "default": null    // ERROR: default must match FIRST union branch
}

// CORRECT: null first when default is null
{
  "name": "email",
  "type": ["null", "string"],
  "default": null
}

// CORRECT: non-null default, non-null type first
{
  "name": "tier",
  "type": ["string", "null"],
  "default": "free"
}
```

### 30.2 Pitfall: Parsing Schema on Every Operation

```go
// WRONG — parses schema on every call
func Encode(record User) []byte {
    schema, _ := avro.Parse(schemaJSON) // O(n) every time
    data, _ := avro.Marshal(schema, record)
    return data
}

// CORRECT — parse once
var schema, _ = avro.Parse(schemaJSON)

func Encode(record User) []byte {
    data, _ := avro.Marshal(schema, record)
    return data
}
```

### 30.3 Pitfall: Not Flushing OCF Writers

```go
enc, _ := ocf.NewEncoder(schemaJSON, file)
for _, record := range records {
    enc.Encode(record)
}
// WRONG: forgot to flush — last partial block may not be written!
file.Close()

// CORRECT
enc.Flush()
file.Close()
```

### 30.4 Pitfall: Schema Evolution Without Defaults

```json
// V1
{"type": "record", "name": "Order", "fields": [
    {"name": "id", "type": "long"}
]}

// V2 — BREAKING: no default for new required field
{"type": "record", "name": "Order", "fields": [
    {"name": "id",     "type": "long"},
    {"name": "status", "type": "string"}  // BREAKING: no default!
]}
// Reading V1 data with V2 schema will throw runtime error!

// V2 — SAFE: default provided
{"type": "record", "name": "Order", "fields": [
    {"name": "id",     "type": "long"},
    {"name": "status", "type": "string", "default": "UNKNOWN"}
]}
```

### 30.5 Pitfall: Changing Field Types Non-Promotably

```json
// V1
{"name": "count", "type": "int"}

// V2 — BREAKING: string is not a promotion of int
{"name": "count", "type": "string"}

// V2 — SAFE: long is a promotion of int
{"name": "count", "type": "long"}
```

### 30.6 Pitfall: Ordering Union Branches Incorrectly

The order of union branches affects:
1. Which type is used for the default value
2. The integer index used in binary encoding (changing order breaks existing data!)

Never reorder union branches in an existing schema deployed to production.

### 30.7 Pitfall: Using float for Monetary Values

```json
// WRONG: floating point cannot represent 0.1 exactly
{"name": "price", "type": "float"}
{"name": "price", "type": "double"}

// CORRECT: use decimal logical type
{"name": "price", "type": {"type": "bytes", "logicalType": "decimal", "precision": 10, "scale": 2}}
```

### 30.8 Pitfall: Ignoring Schema Registry Subject Naming

Using `TopicNameStrategy` with multiple event types on one topic means all events must conform to a single schema — which forces you to use unions. Plan your subject naming strategy before deploying to production.

### 30.9 Pitfall: Not Handling Schema Registry Failures

```go
// Production code must handle registry unavailability
func getSchema(id int32) (avro.Schema, error) {
    // Cache schemas aggressively — registry may be unavailable
    if cached, ok := schemaCache.Load(id); ok {
        return cached.(avro.Schema), nil
    }

    // With timeout and retry
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()

    schema, err := registryClient.GetSchemaByID(ctx, id)
    if err != nil {
        return nil, fmt.Errorf("schema registry unavailable for id %d: %w", id, err)
    }

    schemaCache.Store(id, schema)
    return schema, nil
}
```

---

## 31. Production Best Practices

### 31.1 Schema Governance

1. **Single source of truth**: Store canonical schemas in a version-controlled repository (Git).
2. **CI compatibility checks**: Block PRs that introduce incompatible schema changes.
3. **Schema Registry as deployment gate**: Production Schema Registry rejects incompatible schemas automatically.
4. **Semantic versioning for schemas**: Document breaking vs non-breaking changes in schema changelogs.
5. **Schema review**: Treat schema changes like API changes — they require review and approval.

### 31.2 Operational Schema Registry

```bash
# Health check
curl http://schema-registry:8081/

# Backup all schemas
curl http://schema-registry:8081/subjects | \
  python3 -c "
import json, sys, requests
subjects = json.load(sys.stdin)
backup = {}
for subject in subjects:
    versions = requests.get(f'http://schema-registry:8081/subjects/{subject}/versions').json()
    backup[subject] = {}
    for v in versions:
        schema = requests.get(f'http://schema-registry:8081/subjects/{subject}/versions/{v}').json()
        backup[subject][v] = schema
print(json.dumps(backup, indent=2))
" > schema_backup.json

# Restore from backup
python3 -c "
import json, requests
backup = json.load(open('schema_backup.json'))
for subject, versions in backup.items():
    for v, schema in sorted(versions.items()):
        r = requests.post(
            f'http://schema-registry:8081/subjects/{subject}/versions',
            headers={'Content-Type': 'application/vnd.schemaregistry.v1+json'},
            json={'schema': schema['schema']}
        )
        print(f'{subject} v{v}: {r.json()}')
"
```

### 31.3 Kafka Topic + Schema Checklist

For every new Kafka topic with Avro:
- [ ] Schema designed with evolution in mind (all optional fields have defaults)
- [ ] Schema registered in Schema Registry with `FULL` or `FULL_TRANSITIVE` compatibility
- [ ] Subject naming strategy documented and consistent
- [ ] Consumer-first deployment order documented
- [ ] Schema changelog entry added
- [ ] Integration tests verify schema resolution works
- [ ] Monitoring on schema registry availability

### 31.4 Avro File Management in HDFS

```bash
# Compact small files into larger ones (reduces NameNode pressure)
hadoop jar /opt/hadoop/share/hadoop/tools/lib/hadoop-streaming-*.jar \
    -input /data/orders/year=2024/month=01/day=*/*.avro \
    -output /data/orders/compacted/year=2024/month=01/ \
    -inputformat org.apache.hadoop.hive.ql.io.avro.AvroContainerInputFormat \
    -outputformat org.apache.hadoop.hive.ql.io.avro.AvroContainerOutputFormat \
    -mapper cat \
    -reducer cat \
    -numReduceTasks 4

# Or use Spark for compaction
spark-submit --class com.example.AvroCompactor \
    --conf spark.sql.avro.compression.codec=zstandard \
    compactor.jar \
    /data/orders/year=2024/month=01/day=*/*.avro \
    /data/orders/compacted/
```

### 31.5 Monitoring and Alerting

Key metrics to monitor:

| Metric | Tool | Alert Condition |
|---|---|---|
| Schema Registry request latency | Prometheus | p99 > 500ms |
| Schema Registry error rate | Prometheus | > 0.1% |
| Producer schema registration failures | Kafka client metrics | Any |
| Consumer deserialization errors | Custom metric | Any |
| OCF file block count / file | Custom metric | > 1000 blocks/file |
| Schema compatibility violations | CI/CD gate | Block deployment |

---

## 32. Mental Models for Mastery

### 32.1 The Avro Triad

Every Avro interaction involves three entities:

```
Schema ←→ Datum ←→ Bytes
```

Master the transformations between all three directions. Most developers only know `Datum → Bytes` (serialization) and `Bytes → Datum` (deserialization). Experts also understand `Schema → Schema` (evolution/resolution) and `Bytes → Bytes` (transcoding between codecs).

### 32.2 Schema as Contract, Not Code

In Protocol Buffers, the `.proto` file generates code — the schema IS the code. In Avro, the schema is a **runtime contract**. This is a fundamental cognitive shift:

- In Avro, schemas are **data** that travel with other data.
- Schema resolution is a **computation** done at runtime, not compile time.
- This makes Avro inherently more dynamic and suitable for polyglot systems.

### 32.3 The Two-Audience Mental Model

Every Avro schema has two audiences:

1. **Writers** (producers): Know exactly what they're writing. Must write according to the writer schema.
2. **Readers** (consumers): Know what they need. Use the reader schema. May not know what version they'll receive.

Design schemas from the reader's perspective. Ask: "What is the minimum information a reader needs, and what must always be present vs optional?"

### 32.4 Evolution as a Finite State Machine

Schema evolution is a **finite state machine** where:
- **States** are schema versions (V1, V2, V3...)
- **Transitions** are schema changes (add field, remove field, rename...)
- **Invariant**: Every transition must be backward compatible (or both ways for full compatibility)

Drawing this FSM before writing code is a powerful planning tool. It forces you to think about: "What data will exist in production when V3 is deployed? What schemas will readers have?"

### 32.5 The Chunking Principle (Cognitive)

Avro has many concepts, but they chunk into three layers:

```
Layer 1: Schema Language     → Primitive types, complex types, logical types
Layer 2: Encoding Spec       → Binary encoding, block encoding, union encoding
Layer 3: System Protocols    → OCF format, Schema Registry, RPC
```

Master Layer 1 before Layer 2, and Layer 2 before Layer 3. Many developers jump to Layer 3 (Kafka + Schema Registry) without understanding Layer 2 (why the wire format is compact) or Layer 1 (union defaults must match the first branch type). This leads to cargo-cult usage.

### 32.6 The Deliberate Practice Loop for Avro

```
1. Read a schema → mentally compute the binary encoding by hand
2. Write a schema → check it with avro-tools for validity
3. Evolve a schema → predict compatibility before checking
4. Decode bytes → understand each byte without running code
5. Design a schema for a real system → consider evolution from day one
```

Repeat this loop with progressively more complex schemas. By iteration 20, schema design becomes intuitive.

### 32.7 Pattern Recognition: When Something Feels Wrong

| Smell | Likely Problem |
|---|---|
| Union with `"null"` not first and `default: null` | Schema error — default type must match first union branch |
| Schema parsed inside a hot function | Performance anti-pattern — parse once at startup |
| Adding a field without a default | Breaking change — will fail reading old data |
| Using `double` for money | Use `decimal` logical type |
| Hundreds of tiny Avro files in HDFS | NameNode pressure — compact files |
| Consumer and producer deployed simultaneously | Risky — deploy consumers before producers |
| All fields required (no defaults) | Fragile schema — impossible to evolve safely |

---

## Appendix A: Avro Type Quick Reference

| JSON | Binary Bytes | Go Type | Rust Type | Python Type |
|---|---|---|---|---|
| `"null"` | 0 | `interface{}` (nil) | `()` | `None` |
| `"boolean"` | 1 | `bool` | `bool` | `bool` |
| `"int"` | 1-5 | `int32` | `i32` | `int` |
| `"long"` | 1-9 | `int64` | `i64` | `int` |
| `"float"` | 4 | `float32` | `f32` | `float` |
| `"double"` | 8 | `float64` | `f64` | `float` |
| `"bytes"` | varint+n | `[]byte` | `Vec<u8>` | `bytes` |
| `"string"` | varint+n | `string` | `String` | `str` |
| `"record"` | sum of fields | `struct` | `struct` | `dict` |
| `"enum"` | varint (index) | `string` | `enum` | `str` |
| `"array"` | blocks | `[]T` | `Vec<T>` | `list` |
| `"map"` | blocks | `map[string]T` | `HashMap<String,T>` | `dict` |
| `["null","T"]` | varint+val | `*T` | `Option<T>` | `None\|T` |
| `"fixed"` | exactly n bytes | `[n]byte` | `[u8; N]` | `bytes` |

---

## Appendix B: Schema Compatibility Matrix

| Change | Backward | Forward | Full |
|---|---|---|---|
| Add field with default | ✅ | ✅ | ✅ |
| Add field without default | ❌ | ✅ | ❌ |
| Remove field with default | ✅ | ❌ | ❌ |
| Remove field without default | ❌ | ❌ | ❌ |
| Rename field (with alias) | ✅ | ❌ | ❌ |
| Widen type (int→long) | ✅ | ❌ | ❌ |
| Narrow type (long→int) | ❌ | ✅ | ❌ |
| Add enum symbol (with default) | ✅ | ✅ | ✅ |
| Add enum symbol (no default) | ❌ | ✅ | ❌ |
| Remove enum symbol | ✅ | ❌ | ❌ |
| Add union branch | ✅ | ✅ | ✅ |
| Remove union branch | ❌ | ❌ | ❌ |
| Change namespace | ❌ | ❌ | ❌ |

---

## Appendix C: Essential Resources

- **Avro Specification**: https://avro.apache.org/docs/current/specification/
- **Confluent Schema Registry Docs**: https://docs.confluent.io/platform/current/schema-registry/
- **hamba/avro (Go)**: https://github.com/hamba/avro
- **apache-avro (Rust)**: https://crates.io/crates/apache-avro
- **fastavro (Python)**: https://fastavro.readthedocs.io/
- **avro-tools JAR**: https://repo1.maven.org/maven2/org/apache/avro/avro-tools/
- **Avro IDL Reference**: https://avro.apache.org/docs/current/idl-language/

---

*Master the encoding. Own the evolution. Design for the future.*
*The schema is not just a description of data — it is a contract with time.*

Now let me build the comprehensive Avro guide as a `.md` file.Here's your complete Avro guide — **32 sections, ~12,000 words**, covering everything from the wire format to production Kafka pipelines.

**What's inside:**

The guide is structured in three layers — exactly the chunking model that builds deep mastery:

**Layer 1 — Schema Language** covers all primitive types with their exact binary encoding sizes (the zigzag varint math is explained in full), every complex type (record, enum, array, map, union, fixed), all logical types including the decimal pitfall for financial data, and the full schema namespace/fullname system.

**Layer 2 — Encoding & Evolution** gives you the byte-level wire format with worked hex examples so you can reason about every byte on the wire. The schema resolution rules are presented in full spec-level detail — the two-schema model, backward/forward/full compatibility, the complete compatibility matrix, and renaming fields with aliases.

**Layer 3 — System Protocols** covers OCF file structure and sync markers (why files are Hadoop-splittable), the Confluent 5-byte wire format, Schema Registry REST API and subject naming strategies, Kafka deployment order (consumers before producers), Hive SerDe configuration, Spark schema merging, Flink watermarking with Avro timestamps, and HDFS file management.

**Language coverage**: Go (`hamba/avro`) and Rust (`apache-avro`) are covered with idiomatic, production-grade examples including `sync.OnceLock` for schema caching in Rust, OCF writer/reader patterns, schema resolution, Confluent encoding helpers, and benchmarking harnesses. Python (`fastavro`) and C (`libavro-c`) are included as reference.

**Section 30** (Common Pitfalls) and **Section 32** (Mental Models) are the ones to internalize deeply — they encode the expert intuition that separates someone who uses Avro from someone who truly understands it.