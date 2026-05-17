Great question! You're right that most foundational DSA were established before 2000. But the 2000s onward brought significant innovations, driven by the internet, big data, machine learning, and distributed systems. Here's a rundown:

---

## 📦 Data Structures (Post-2000)

**Cache-Oblivious & Memory-Efficient Structures**
- **Cache-oblivious B-trees** (2000) — Brodal & Fagerberg; optimal for memory hierarchy without knowing cache size
- **van Emde Boas trees** were *popularized* post-2000 in practice, though invented earlier

**Probabilistic & Approximate Structures**
- **Count-Min Sketch** (2003, Cormode & Muthukrishnan) — frequency estimation in streams
- **HyperLogLog** (2007, Flajolet et al.) — cardinality estimation with tiny memory; used everywhere (Redis, Google)
- **Cuckoo Filter** (2014) — better than Bloom filters; supports deletions

**Succinct & Compressed Structures**
- **FM-Index** (2000, Ferragina & Manzini) — compressed full-text index; backbone of modern DNA search (BWA, Bowtie)
- **Wavelet Trees** (2003) — range queries on sequences; used in bioinformatics
- **Compressed Suffix Arrays** — practical genome sequencing

**Concurrent & Distributed**
- **Skip list variants** for concurrent access (2000s)
- **CRDT (Conflict-free Replicated Data Types)** (2011) — used in Google Docs, collaborative apps
- **LSM Tree** (*popularized* post-2000) — backbone of LevelDB, RocksDB, Cassandra, HBase

**Graph & Spatial**
- **PH-Tree** (2014) — multi-dimensional indexing
- **Fractal Tree Index** (2007, Tokutek) — write-optimized B-tree variant

---

## ⚙️ Algorithms (Post-2000)

**String & Text**
- **Burrows-Wheeler Aligner (BWA)** (2009) — DNA sequence alignment
- **Aho-Corasick improvements** and cache-efficient string matching

**Graph Algorithms**
- **Thorup's linear-time SSSP** for undirected graphs (1999–2000)
- **Compressed sparse row optimizations** for modern hardware
- **Triangle counting algorithms** for social networks (2000s–2010s)
- **Girvan-Newman community detection** (2002)
- **Label Propagation** (2007) — fast community detection

**Sorting & Searching**
- **Timsort** (2002, Tim Peters) — now default in Python, Java, Android; hybrid merge+insertion sort
- **pdqsort / Pattern-Defeating Quicksort** (2015) — used in Rust, C++ Boost

**Randomized & Streaming**
- **Reservoir Sampling improvements** for distributed streams
- **Locality-Sensitive Hashing (LSH)** — *heavily developed* post-2000 for nearest-neighbor search
- **MinHash** (widely adopted post-2000) — document similarity at scale (used by Google, Spotify)

**Compression**
- **Zstandard (Zstd)** (2016, Facebook) — modern compression algorithm
- **Brotli** (2015, Google) — web compression
- **LZ4** (2011) — ultra-fast compression

**Machine Learning Algorithms** (a category that exploded)
- **Random Forests** (2001, Breiman)
- **Gradient Boosting / XGBoost** (refined 2000s–2016)
- **HNSW** (2016) — Hierarchical Navigable Small World graphs; the go-to algorithm for vector search (used in Pinecone, Weaviate, FAISS)
- **Transformer attention mechanism** (2017) — arguably the most impactful algorithm of the 2000s era

**Distributed Systems Algorithms**
- **Raft consensus** (2014) — simpler alternative to Paxos; used in etcd, CockroachDB
- **Consistent Hashing** (*popularized* by Amazon Dynamo paper, 2007)
- **MapReduce** (2004, Google) — parallel data processing paradigm
- **Chord / Kademlia DHT** (2001) — distributed hash tables for P2P networks

---

## 🧠 The Big Theme

| Era | Driven by |
|---|---|
| Pre-2000 | Theoretical CS, compilers, databases |
| 2000–2010 | Internet scale, search engines, P2P |
| 2010–2020 | Big data, cloud, genomics, social graphs |
| 2020+ | ML/AI, vector search, real-time streaming |

The modern frontier is **vector search algorithms** (HNSW, IVF, FAISS) and **streaming/approximate algorithms** — both essential for AI applications today.

Succinct Data Structures
Swiss Tables 
Cuckoo Hashing
Retroactive Data Structures
Left-Leaning Red-Black Trees