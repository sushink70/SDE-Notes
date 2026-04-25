# Complete Go Programming Guide for Cloud-Native Networking
## From Zero to Production-Ready

---

> **Who this guide is for:** Engineers preparing to build cloud-native networking projects (service meshes, CNI plugins, proxies, load balancers, API gateways, network controllers) using Go. Every concept here is mandatory — not optional background reading.

---

## Table of Contents

1. [Go Fundamentals & Toolchain](#1-go-fundamentals--toolchain)
2. [Variables, Types & Constants](#2-variables-types--constants)
3. [Control Flow](#3-control-flow)
4. [Functions — First-Class Citizens](#4-functions--first-class-citizens)
5. [Pointers — Deep Understanding](#5-pointers--deep-understanding)
6. [Arrays, Slices & Maps](#6-arrays-slices--maps)
7. [Structs & Methods](#7-structs--methods)
8. [Interfaces — The Heart of Go](#8-interfaces--the-heart-of-go)
9. [Error Handling — Production Patterns](#9-error-handling--production-patterns)
10. [Defer, Panic & Recover](#10-defer-panic--recover)
11. [Packages, Modules & Dependency Management](#11-packages-modules--dependency-management)
12. [Goroutines — Concurrency Model](#12-goroutines--concurrency-model)
13. [Channels — Communication Primitives](#13-channels--communication-primitives)
14. [The `select` Statement](#14-the-select-statement)
15. [Sync Package — Synchronization Primitives](#15-sync-package--synchronization-primitives)
16. [Context Package — Cancellation & Deadlines](#16-context-package--cancellation--deadlines)
17. [The `net` Package — Low-Level Networking](#17-the-net-package--low-level-networking)
18. [HTTP Client & Server (`net/http`)](#18-http-client--server-nethttp)
19. [TLS & Secure Communication](#19-tls--secure-communication)
20. [Encoding: JSON, Binary & Protocol Buffers](#20-encoding-json-binary--protocol-buffers)
21. [gRPC in Go](#21-grpc-in-go)
22. [Timers, Tickers & Scheduling](#22-timers-tickers--scheduling)
23. [File I/O & OS Interaction](#23-file-io--os-interaction)
24. [Reflection & the `unsafe` Package](#24-reflection--the-unsafe-package)
25. [Generics (Go 1.18+)](#25-generics-go-118)
26. [Testing — Unit, Integration & Benchmarks](#26-testing--unit-integration--benchmarks)
27. [Profiling & Performance Optimization](#27-profiling--performance-optimization)
28. [Memory Model & Garbage Collection](#28-memory-model--garbage-collection)
29. [Build System, CGo & Syscalls](#29-build-system-cgo--syscalls)
30. [Cloud-Native Patterns in Go](#30-cloud-native-patterns-in-go)

---

## 1. Go Fundamentals & Toolchain

### 1.1 Why Go for Cloud-Native Networking?

Go was purpose-built for the problems that cloud-native networking solves:

- **Static single binary**: No runtime dependencies, perfect for containers
- **Built-in concurrency**: Goroutines handle thousands of simultaneous connections efficiently
- **Garbage collected but predictable**: Low-latency GC tunable for networking workloads
- **Standard library**: `net`, `net/http`, `crypto/tls` are production-grade out of the box
- **Cross-compilation**: Build Linux ARM64 binaries from a macOS x86 machine trivially
- **Fast compilation**: The entire Kubernetes codebase compiles in seconds

Projects like Kubernetes, Istio, Envoy's control plane, Cilium, Calico, CoreDNS, Traefik, and Consul are all written in Go.

### 1.2 Installing Go & Workspace Setup

```bash
# Download and install
wget https://go.dev/dl/go1.22.0.linux-amd64.tar.gz
sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xzf go1.22.0.linux-amd64.tar.gz

# Add to PATH in ~/.bashrc or ~/.zshrc
export PATH=$PATH:/usr/local/go/bin
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin

# Verify
go version
# go version go1.22.0 linux/amd64
```

### 1.3 Essential Go Commands

```bash
# Initialize a new module
go mod init github.com/yourname/networkproject

# Add a dependency
go get github.com/some/package@v1.2.3

# Tidy up go.mod and go.sum
go mod tidy

# Build a binary
go build -o bin/myapp ./cmd/myapp/

# Cross-compile for Linux from macOS
GOOS=linux GOARCH=amd64 go build -o bin/myapp-linux ./cmd/myapp/

# Run tests
go test ./...

# Run with race detector (MANDATORY in networking code)
go test -race ./...

# Format code
gofmt -w .
# or
goimports -w .

# Vet (static analysis)
go vet ./...

# Run linter
golangci-lint run

# Generate code (protobuf, mocks, etc.)
go generate ./...

# Build with version information embedded
go build -ldflags="-X main.version=v1.0.0 -X main.buildTime=$(date -u +%Y%m%dT%H%M%SZ)" ./...
```

### 1.4 Project Structure for Cloud-Native Projects

```
mynetworkproject/
├── cmd/
│   ├── agent/
│   │   └── main.go          # Entry point for agent binary
│   └── controller/
│       └── main.go          # Entry point for controller binary
├── pkg/
│   ├── networking/          # Core networking logic
│   ├── proxy/               # Proxy implementation
│   └── config/              # Configuration parsing
├── internal/
│   ├── dataplane/           # Internal-only packages
│   └── metrics/
├── api/
│   └── v1/
│       └── types.go         # API type definitions
├── proto/
│   └── service.proto        # Protobuf definitions
├── hack/
│   └── update-codegen.sh    # Code generation scripts
├── Makefile
├── Dockerfile
├── go.mod
├── go.sum
└── README.md
```

---

## 2. Variables, Types & Constants

### 2.1 Variable Declaration — All Forms

```go
package main

import "fmt"

func main() {
    // Long form — explicit type
    var port int = 8080

    // Long form — type inferred
    var host = "localhost"

    // Short form — only inside functions
    protocol := "tcp"

    // Multiple declarations
    var (
        maxConnections = 1000
        readTimeout    = 30
        writeTimeout   = 30
    )

    // Zero values — crucial to understand
    var i int        // 0
    var f float64    // 0.0
    var b bool       // false
    var s string     // ""
    var p *int       // nil
    var sl []byte    // nil
    var m map[string]int // nil

    fmt.Println(port, host, protocol, maxConnections, readTimeout, writeTimeout)
    fmt.Println(i, f, b, s, p, sl, m)
}
```

### 2.2 Built-in Types

```go
package main

import (
    "fmt"
    "math"
    "unsafe"
)

func main() {
    // Integer types — size matters in networking (packet headers, syscalls)
    var i8  int8   = 127           // -128 to 127
    var i16 int16  = 32767         // TCP port range: 0-65535
    var i32 int32  = 2147483647    // IPv4 address (uint32)
    var i64 int64  = math.MaxInt64
    var u8  uint8  = 255           // byte — single octet in network packets
    var u16 uint16 = 65535         // Port numbers: 0-65535
    var u32 uint32 = 4294967295    // IPv4 address space
    var u64 uint64 = math.MaxUint64

    // Platform-dependent
    var i   int   = 100  // 64-bit on 64-bit platforms
    var u   uint  = 100
    var ptr uintptr = 0  // for pointer arithmetic

    // Floating point
    var f32 float32 = 3.14
    var f64 float64 = 3.141592653589793

    // Complex (rarely used in networking)
    var c64  complex64  = 1 + 2i
    var c128 complex128 = 3 + 4i

    // Boolean
    var connected bool = true

    // String — immutable sequence of bytes
    var addr string = "192.168.1.1"

    // byte is alias for uint8
    var b byte = 0xFF

    // rune is alias for int32 (Unicode code point)
    var r rune = '✓'

    fmt.Println(i8, i16, i32, i64, u8, u16, u32, u64)
    fmt.Println(i, u, ptr)
    fmt.Println(f32, f64, c64, c128)
    fmt.Println(connected, addr, b, r)

    // Sizes matter for networking
    fmt.Printf("uint8 size:  %d bytes\n", unsafe.Sizeof(u8))
    fmt.Printf("uint16 size: %d bytes\n", unsafe.Sizeof(u16))
    fmt.Printf("uint32 size: %d bytes\n", unsafe.Sizeof(u32))
}
```

### 2.3 Constants & iota

```go
package main

import "fmt"

// Typed constants
const MaxPacketSize = 65535
const DefaultMTU = 1500

// iota — extremely useful for flags, states, and protocols
type ConnectionState int

const (
    StateNew ConnectionState = iota // 0
    StateActive                     // 1
    StateIdle                       // 2
    StateClosing                    // 3
    StateClosed                     // 4
)

func (s ConnectionState) String() string {
    switch s {
    case StateNew:
        return "NEW"
    case StateActive:
        return "ACTIVE"
    case StateIdle:
        return "IDLE"
    case StateClosing:
        return "CLOSING"
    case StateClosed:
        return "CLOSED"
    default:
        return "UNKNOWN"
    }
}

// Bit flags using iota — used in network feature flags
type Feature uint32

const (
    FeatureTLS         Feature = 1 << iota // 1
    FeatureCompression                     // 2
    FeatureKeepAlive                       // 4
    FeatureHTTP2                           // 8
    FeatureWebSocket                       // 16
)

// Byte size constants using iota with expressions
const (
    _           = iota             // ignore first value
    KB = 1 << (10 * iota)         // 1024
    MB                            // 1048576
    GB                            // 1073741824
    TB                            // 1099511627776
)

func main() {
    state := StateActive
    fmt.Println(state) // ACTIVE

    // Combining feature flags
    features := FeatureTLS | FeatureHTTP2 | FeatureKeepAlive

    // Checking a specific flag
    if features&FeatureTLS != 0 {
        fmt.Println("TLS enabled")
    }

    fmt.Printf("KB: %d, MB: %d, GB: %d\n", KB, MB, GB)
}
```

### 2.4 Type Conversions & Type Aliases

```go
package main

import (
    "encoding/binary"
    "fmt"
    "net"
)

// Type alias — same underlying type, used for semantic meaning
type IPAddress = net.IP

// Named type — new type with same underlying type
type Port uint16
type Protocol string

const (
    TCP Protocol = "tcp"
    UDP Protocol = "udp"
)

func main() {
    // Explicit type conversion — always required in Go
    var port Port = 8080
    var rawPort uint16 = uint16(port) // explicit conversion
    fmt.Println(rawPort)

    // Integer to string is NOT what you think
    n := 65
    s := string(rune(n)) // "A" — converts to Unicode char
    fmt.Println(s)

    // Correct way: use fmt or strconv
    // s := fmt.Sprintf("%d", n) // "65"

    // Network byte order (big-endian) conversion — critical in networking
    buf := make([]byte, 2)
    binary.BigEndian.PutUint16(buf, uint16(port))
    fmt.Printf("Port %d in network bytes: %v\n", port, buf)
    
    recovered := binary.BigEndian.Uint16(buf)
    fmt.Printf("Recovered port: %d\n", recovered)

    // IPv4 to uint32 — common in network programming
    ip := net.ParseIP("192.168.1.1").To4()
    ipInt := binary.BigEndian.Uint32(ip)
    fmt.Printf("IP as uint32: %d\n", ipInt)
}
```

---

## 3. Control Flow

### 3.1 if/else — Go Style

```go
package main

import (
    "fmt"
    "net"
)

func checkConnection(address string) error {
    // Init statement in if — scopes err to the if block
    if conn, err := net.Dial("tcp", address); err != nil {
        return fmt.Errorf("connection failed: %w", err)
    } else {
        defer conn.Close()
        fmt.Printf("Connected to %s\n", conn.RemoteAddr())
    }
    return nil
}

func classifyPort(port int) string {
    if port < 0 || port > 65535 {
        return "invalid"
    } else if port < 1024 {
        return "well-known"
    } else if port < 49152 {
        return "registered"
    } else {
        return "dynamic/private"
    }
}

func main() {
    fmt.Println(classifyPort(80))    // well-known
    fmt.Println(classifyPort(8080))  // registered
    fmt.Println(classifyPort(55000)) // dynamic/private
}
```

### 3.2 switch — Powerful in Go

```go
package main

import (
    "fmt"
    "net"
)

func handleProtocol(proto string) {
    // switch without condition = if-else chain
    switch {
    case proto == "tcp" || proto == "tcp4" || proto == "tcp6":
        fmt.Println("TCP connection")
    case proto == "udp" || proto == "udp4" || proto == "udp6":
        fmt.Println("UDP datagram")
    case proto == "unix" || proto == "unixpacket":
        fmt.Println("Unix socket")
    default:
        fmt.Printf("Unknown protocol: %s\n", proto)
    }
}

func handleAddr(addr net.Addr) {
    // Type switch — critical for interface handling
    switch a := addr.(type) {
    case *net.TCPAddr:
        fmt.Printf("TCP: %s:%d (IPv%d)\n", a.IP, a.Port, ipVersion(a.IP))
    case *net.UDPAddr:
        fmt.Printf("UDP: %s:%d\n", a.IP, a.Port)
    case *net.UnixAddr:
        fmt.Printf("Unix socket: %s (%s)\n", a.Name, a.Net)
    case *net.IPAddr:
        fmt.Printf("IP: %s\n", a.IP)
    default:
        fmt.Printf("Unknown address type: %T\n", a)
    }
}

func ipVersion(ip net.IP) int {
    if ip.To4() != nil {
        return 4
    }
    return 6
}

func main() {
    handleProtocol("tcp")
    handleProtocol("udp")
    
    tcpAddr := &net.TCPAddr{IP: net.ParseIP("10.0.0.1"), Port: 443}
    handleAddr(tcpAddr)
}
```

### 3.3 for — The Only Loop in Go

```go
package main

import (
    "fmt"
    "time"
)

func main() {
    // C-style for loop
    for i := 0; i < 3; i++ {
        fmt.Println(i)
    }

    // while-equivalent
    retries := 0
    for retries < 3 {
        fmt.Printf("Attempt %d\n", retries+1)
        retries++
    }

    // Infinite loop — common in servers and network listeners
    // for {
    //     conn, err := listener.Accept()
    //     if err != nil { break }
    //     go handleConn(conn)
    // }

    // Range over slice
    servers := []string{"10.0.0.1:8080", "10.0.0.2:8080", "10.0.0.3:8080"}
    for i, server := range servers {
        fmt.Printf("[%d] %s\n", i, server)
    }

    // Range over map
    portNames := map[int]string{80: "HTTP", 443: "HTTPS", 22: "SSH"}
    for port, name := range portNames {
        fmt.Printf("%d -> %s\n", port, name)
    }

    // Range over string — iterates runes, not bytes
    for i, r := range "hello" {
        fmt.Printf("index %d: %c\n", i, r)
    }

    // Range over channel — reads until closed
    ch := make(chan int, 3)
    ch <- 1; ch <- 2; ch <- 3
    close(ch)
    for v := range ch {
        fmt.Println(v)
    }

    // for with labels — break/continue to outer loop
    outer:
    for i := 0; i < 3; i++ {
        for j := 0; j < 3; j++ {
            if i == 1 && j == 1 {
                break outer // breaks the outer loop
            }
            fmt.Printf("(%d,%d) ", i, j)
        }
    }
    fmt.Println()

    // Ticker loop — polling pattern in networking agents
    ticker := time.NewTicker(100 * time.Millisecond)
    defer ticker.Stop()
    count := 0
    for range ticker.C {
        count++
        if count >= 3 {
            break
        }
        fmt.Println("tick")
    }
}
```

---

## 4. Functions — First-Class Citizens

### 4.1 Function Signatures & Multiple Return Values

```go
package main

import (
    "errors"
    "fmt"
    "net"
)

// Basic function
func add(a, b int) int {
    return a + b
}

// Multiple return values — idiomatic Go (value + error)
func resolve(host string) (net.IP, error) {
    addrs, err := net.LookupHost(host)
    if err != nil {
        return nil, fmt.Errorf("DNS lookup failed for %s: %w", host, err)
    }
    if len(addrs) == 0 {
        return nil, errors.New("no addresses found")
    }
    return net.ParseIP(addrs[0]), nil
}

// Named return values — useful for documentation and defer
func parseAddress(addr string) (host string, port string, err error) {
    host, port, err = net.SplitHostPort(addr)
    if err != nil {
        err = fmt.Errorf("invalid address %q: %w", addr, err)
        return // naked return — returns named values
    }
    return
}

// Variadic functions
func joinAddresses(sep string, addrs ...string) string {
    result := ""
    for i, addr := range addrs {
        if i > 0 {
            result += sep
        }
        result += addr
    }
    return result
}

// Functions as parameters — used heavily in middleware patterns
type HandlerFunc func(conn net.Conn) error

type Middleware func(HandlerFunc) HandlerFunc

func withLogging(next HandlerFunc) HandlerFunc {
    return func(conn net.Conn) error {
        fmt.Printf("Connection from %s\n", conn.RemoteAddr())
        err := next(conn)
        if err != nil {
            fmt.Printf("Handler error: %v\n", err)
        }
        return err
    }
}

func withRecovery(next HandlerFunc) HandlerFunc {
    return func(conn net.Conn) error {
        defer func() {
            if r := recover(); r != nil {
                fmt.Printf("Recovered from panic: %v\n", r)
            }
        }()
        return next(conn)
    }
}

// Function returning a function — closures for configuration
func newRetryer(maxRetries int) func(fn func() error) error {
    return func(fn func() error) error {
        var lastErr error
        for i := 0; i < maxRetries; i++ {
            if err := fn(); err == nil {
                return nil
            } else {
                lastErr = err
                fmt.Printf("Retry %d/%d: %v\n", i+1, maxRetries, err)
            }
        }
        return fmt.Errorf("failed after %d retries: %w", maxRetries, lastErr)
    }
}

func main() {
    ip, err := resolve("localhost")
    if err != nil {
        fmt.Println("Error:", err)
    } else {
        fmt.Println("Resolved:", ip)
    }

    host, port, err := parseAddress("10.0.0.1:8080")
    if err != nil {
        fmt.Println("Error:", err)
    } else {
        fmt.Printf("Host: %s, Port: %s\n", host, port)
    }

    fmt.Println(joinAddresses(", ", "10.0.0.1", "10.0.0.2", "10.0.0.3"))

    retry := newRetryer(3)
    attempts := 0
    retry(func() error {
        attempts++
        if attempts < 3 {
            return errors.New("not ready")
        }
        return nil
    })
}
```

### 4.2 Closures — Capturing State

```go
package main

import (
    "fmt"
    "sync/atomic"
)

// Counter using closure — thread-safe with atomic
func newCounter() func() uint64 {
    var count uint64
    return func() uint64 {
        return atomic.AddUint64(&count, 1)
    }
}

// Connection pool generator using closure
func newConnectionPool(size int) (acquire func() int, release func(int)) {
    pool := make(chan int, size)
    for i := 0; i < size; i++ {
        pool <- i
    }

    acquire = func() int {
        return <-pool
    }

    release = func(id int) {
        pool <- id
    }

    return
}

// Rate limiter using closure
func newRateLimiter(rps int) func() bool {
    tokens := make(chan struct{}, rps)
    // Fill initial tokens
    for i := 0; i < rps; i++ {
        tokens <- struct{}{}
    }
    return func() bool {
        select {
        case <-tokens:
            return true
        default:
            return false
        }
    }
}

func main() {
    counter := newCounter()
    fmt.Println(counter()) // 1
    fmt.Println(counter()) // 2
    fmt.Println(counter()) // 3

    acquire, release := newConnectionPool(3)
    id1 := acquire()
    id2 := acquire()
    fmt.Printf("Got connections: %d, %d\n", id1, id2)
    release(id1)
    id3 := acquire()
    fmt.Printf("Reused connection: %d\n", id3)
}
```

### 4.3 init() Functions

```go
package main

import (
    "fmt"
    "net"
)

var defaultResolver *net.Resolver

// init() runs before main(), after all variable initializations
// Multiple init() functions can exist in the same package
func init() {
    defaultResolver = &net.Resolver{
        PreferGo: true,
        Dial: func(ctx interface{}, network, address string) (net.Conn, error) {
            // Custom DNS resolver setup
            return net.Dial("udp", "8.8.8.8:53")
        },
    }
    fmt.Println("Resolver initialized")
}

func init() {
    // Second init() in the same file — both will run
    fmt.Println("Additional initialization")
}

func main() {
    fmt.Println("Main started")
    // defaultResolver is ready to use
}
```

---

## 5. Pointers — Deep Understanding

### 5.1 Pointer Basics & Patterns

```go
package main

import (
    "fmt"
    "sync"
)

// Pointer fundamentals
func main() {
    x := 42
    p := &x // p is *int, holds the address of x

    fmt.Printf("Value: %d\n", x)
    fmt.Printf("Address: %p\n", p)
    fmt.Printf("Dereferenced: %d\n", *p)

    *p = 100 // Modifying through pointer
    fmt.Printf("After modification: %d\n", x) // 100

    // nil pointer — must check before dereferencing
    var np *int
    fmt.Println(np == nil) // true
    // fmt.Println(*np) // PANIC: nil pointer dereference

    // new() — allocates zeroed memory
    pp := new(int) // equivalent to: pp := &(0)
    *pp = 8080
    fmt.Println(*pp)
}

// When to use pointers:
// 1. Large structs — avoid copying
// 2. Mutation — modify the caller's value
// 3. Optional values — nil means absent
// 4. Sharing — multiple goroutines reference the same data

type ConnectionConfig struct {
    Host     string
    Port     int
    MaxConns int
    TLS      bool
    mu       sync.Mutex // Must not be copied — always use pointer receiver
}

// Pointer receiver — required when:
// - Method mutates the struct
// - Struct has sync primitives (Mutex, WaitGroup)
// - Struct is large (avoid copying overhead)
func (c *ConnectionConfig) SetHost(host string) {
    c.Host = host
}

// Value receiver — for read-only, small structs
func (c ConnectionConfig) Address() string {
    return fmt.Sprintf("%s:%d", c.Host, c.Port)
}

// Passing large structs — always as pointer
func validateConfig(cfg *ConnectionConfig) error {
    if cfg == nil {
        return fmt.Errorf("config is nil")
    }
    if cfg.Host == "" {
        return fmt.Errorf("host is required")
    }
    if cfg.Port <= 0 || cfg.Port > 65535 {
        return fmt.Errorf("invalid port: %d", cfg.Port)
    }
    return nil
}

// Double pointer — modifying a pointer itself
func initConfig(cfg **ConnectionConfig) {
    if *cfg == nil {
        *cfg = &ConnectionConfig{
            Host:     "localhost",
            Port:     8080,
            MaxConns: 100,
        }
    }
}
```

---

## 6. Arrays, Slices & Maps

### 6.1 Arrays — Fixed Size

```go
package main

import "fmt"

func main() {
    // Arrays have fixed size — used for fixed-size network headers
    var ipv4Header [20]byte    // Minimum IPv4 header
    var ethernetFrame [14]byte // Ethernet frame header
    
    // Size is part of the type — [4]byte != [20]byte
    ipv4Header[0] = 0x45      // Version=4, IHL=5
    ipv4Header[9] = 0x06      // Protocol: TCP

    fmt.Printf("IPv4 Header: %v\n", ipv4Header[:10])
    fmt.Println(ethernetFrame) // zero-valued

    // Arrays are value types — copying makes a full copy
    a := [3]int{1, 2, 3}
    b := a // full copy
    b[0] = 99
    fmt.Println(a[0]) // 1 — unaffected
    fmt.Println(b[0]) // 99

    // Compare arrays — valid for same-size arrays of comparable types
    x := [3]int{1, 2, 3}
    y := [3]int{1, 2, 3}
    fmt.Println(x == y) // true
}
```

### 6.2 Slices — Dynamic, Flexible, Critical

```go
package main

import (
    "fmt"
    "net"
)

func main() {
    // Slice = pointer to array + length + capacity
    // This is the MOST IMPORTANT data structure in Go networking

    // Creating slices
    s1 := []byte{0x45, 0x00, 0x00, 0x28} // IPv4 header start
    s2 := make([]byte, 20)                 // length=20, cap=20, all zeros
    s3 := make([]byte, 0, 1500)            // length=0, cap=1500 (MTU-sized buffer)

    fmt.Println(len(s1), cap(s1))  // 4 4
    fmt.Println(len(s2), cap(s2))  // 20 20
    fmt.Println(len(s3), cap(s3))  // 0 1500

    // Appending
    s3 = append(s3, 0x01, 0x02, 0x03)
    fmt.Println(len(s3), cap(s3))  // 3 1500 — no reallocation

    // Slicing a slice — creates a view, NOT a copy
    data := make([]byte, 1500)
    header := data[:20]   // IPv4 header view
    payload := data[20:]  // Payload view
    
    // DANGER: modifying header modifies data too!
    header[0] = 0x45
    fmt.Println(data[0]) // 0x45

    // Copy to avoid this sharing
    safeHeader := make([]byte, 20)
    copy(safeHeader, data[:20])

    // Three-index slice — limits capacity (prevents writing beyond)
    limited := data[0:20:20]  // len=20, cap=20, not data[20:]
    fmt.Println(len(limited), cap(limited))

    // Growing slices — capacity doubles when exceeded
    var packets [][]byte
    for i := 0; i < 5; i++ {
        pkt := make([]byte, 64)
        packets = append(packets, pkt)
    }

    // Deleting from slice without preserving order (fast)
    i := 2 // delete index 2
    packets[i] = packets[len(packets)-1]
    packets[len(packets)-1] = nil // prevent memory leak
    packets = packets[:len(packets)-1]

    // Deleting from slice preserving order (slower — O(n))
    // packets = append(packets[:i], packets[i+1:]...)

    // Reading from network into a reusable slice buffer
    buf := make([]byte, 65535) // max UDP packet size
    listener, _ := net.ListenPacket("udp", "127.0.0.1:0")
    defer listener.Close()
    // n, addr, _ := listener.ReadFrom(buf)
    // packet := buf[:n]  // slice to actual data read
    _ = buf

    // nil vs empty slice — both have len 0 but nil is nil
    var nilSlice []byte
    emptySlice := []byte{}
    emptySlice2 := make([]byte, 0)
    
    fmt.Println(nilSlice == nil)   // true
    fmt.Println(emptySlice == nil) // false
    fmt.Println(emptySlice2 == nil)// false
    
    // Both are safe to append to and range over
    nilSlice = append(nilSlice, 1, 2, 3)
    fmt.Println(nilSlice)
}
```

### 6.3 Maps — Hash Tables

```go
package main

import (
    "fmt"
    "net"
    "sync"
)

func main() {
    // Map creation
    portServices := map[int]string{
        80:   "http",
        443:  "https",
        22:   "ssh",
        53:   "dns",
        8080: "http-alt",
    }

    // Lookup with existence check — ALWAYS use this pattern
    if service, ok := portServices[443]; ok {
        fmt.Println("Port 443:", service)
    }

    // Lookup of missing key returns zero value — NOT an error
    svc := portServices[9999] // ""
    fmt.Printf("Port 9999: %q\n", svc) // ""

    // Delete
    delete(portServices, 8080)

    // Iterate — order is NOT guaranteed (by design)
    for port, svc := range portServices {
        fmt.Printf("%d: %s\n", port, svc)
    }

    // Map of slices — connection tracking table
    connectionTable := make(map[string][]net.Conn)
    
    // Maps with struct values — flow table
    type FlowKey struct {
        SrcIP   string
        DstIP   string
        SrcPort uint16
        DstPort uint16
        Proto   string
    }
    type FlowStats struct {
        Packets uint64
        Bytes   uint64
    }

    flowTable := make(map[FlowKey]*FlowStats)
    key := FlowKey{"10.0.0.1", "10.0.0.2", 55123, 80, "tcp"}
    flowTable[key] = &FlowStats{Packets: 1, Bytes: 1500}
    flowTable[key].Packets++

    _ = connectionTable
    fmt.Println(flowTable[key])
}

// Thread-safe map using sync.Map — for concurrent networking code
type ConnectionRegistry struct {
    connections sync.Map // map[string]net.Conn
}

func (r *ConnectionRegistry) Register(id string, conn net.Conn) {
    r.connections.Store(id, conn)
}

func (r *ConnectionRegistry) Get(id string) (net.Conn, bool) {
    val, ok := r.connections.Load(id)
    if !ok {
        return nil, false
    }
    return val.(net.Conn), true
}

func (r *ConnectionRegistry) Remove(id string) {
    r.connections.Delete(id)
}

func (r *ConnectionRegistry) ForEach(fn func(id string, conn net.Conn)) {
    r.connections.Range(func(key, val interface{}) bool {
        fn(key.(string), val.(net.Conn))
        return true // continue iteration
    })
}

// Thread-safe map using RWMutex — more control than sync.Map
type RouteTable struct {
    mu     sync.RWMutex
    routes map[string]string // destination CIDR -> next hop
}

func NewRouteTable() *RouteTable {
    return &RouteTable{routes: make(map[string]string)}
}

func (rt *RouteTable) Add(cidr, nextHop string) {
    rt.mu.Lock()
    defer rt.mu.Unlock()
    rt.routes[cidr] = nextHop
}

func (rt *RouteTable) Lookup(cidr string) (string, bool) {
    rt.mu.RLock()
    defer rt.mu.RUnlock()
    nh, ok := rt.routes[cidr]
    return nh, ok
}

func (rt *RouteTable) Snapshot() map[string]string {
    rt.mu.RLock()
    defer rt.mu.RUnlock()
    snap := make(map[string]string, len(rt.routes))
    for k, v := range rt.routes {
        snap[k] = v
    }
    return snap
}
```

---

## 7. Structs & Methods

### 7.1 Struct Design Patterns

```go
package main

import (
    "fmt"
    "net"
    "sync"
    "time"
)

// Basic struct
type Endpoint struct {
    Host string
    Port int
}

func (e Endpoint) String() string {
    return fmt.Sprintf("%s:%d", e.Host, e.Port)
}

func (e Endpoint) Addr() net.Addr {
    addr, _ := net.ResolveTCPAddr("tcp", e.String())
    return addr
}

// Embedded structs — composition over inheritance
type BaseEndpoint struct {
    Endpoint
    Protocol string
    Weight   int
}

type HealthStatus struct {
    Healthy     bool
    LastCheck   time.Time
    Failures    int
    SuccessRate float64
}

// Composed struct using embedding
type BackendServer struct {
    BaseEndpoint           // embedded — promotes all fields and methods
    HealthStatus           // embedded — promotes health fields
    ID          string
    Labels      map[string]string
    mu          sync.RWMutex // unexported — not embedded, just a field
}

func NewBackendServer(id, host string, port int) *BackendServer {
    return &BackendServer{
        BaseEndpoint: BaseEndpoint{
            Endpoint: Endpoint{Host: host, Port: port},
            Protocol: "tcp",
            Weight:   1,
        },
        HealthStatus: HealthStatus{
            Healthy:   true,
            LastCheck: time.Now(),
        },
        ID:     id,
        Labels: make(map[string]string),
    }
}

// Method on embedded promotes to outer struct
func (b *BackendServer) IsAvailable() bool {
    b.mu.RLock()
    defer b.mu.RUnlock()
    return b.Healthy && b.Failures < 5
}

func (b *BackendServer) RecordFailure() {
    b.mu.Lock()
    defer b.mu.Unlock()
    b.Failures++
    b.Healthy = b.Failures < 5
    b.LastCheck = time.Now()
}

func (b *BackendServer) RecordSuccess() {
    b.mu.Lock()
    defer b.mu.Unlock()
    if b.Failures > 0 {
        b.Failures--
    }
    b.Healthy = true
    b.LastCheck = time.Now()
}

// Struct tags — used for JSON, protobuf, validation
type NetworkPolicy struct {
    Name      string            `json:"name" yaml:"name"`
    Namespace string            `json:"namespace" yaml:"namespace"`
    Selector  map[string]string `json:"selector,omitempty" yaml:"selector,omitempty"`
    Ingress   []IngressRule     `json:"ingress" yaml:"ingress"`
    Egress    []EgressRule      `json:"egress,omitempty" yaml:"egress,omitempty"`
}

type IngressRule struct {
    From  []NetworkPeer `json:"from"`
    Ports []PortRule    `json:"ports,omitempty"`
}

type EgressRule struct {
    To    []NetworkPeer `json:"to"`
    Ports []PortRule    `json:"ports,omitempty"`
}

type NetworkPeer struct {
    CIDR      string            `json:"cidr,omitempty"`
    PodLabels map[string]string `json:"podLabels,omitempty"`
}

type PortRule struct {
    Port     int    `json:"port"`
    Protocol string `json:"protocol"`
}

// Anonymous structs — useful for one-off structures and JSON
func createHealthCheckPayload(server *BackendServer) interface{} {
    return struct {
        ID      string `json:"id"`
        Address string `json:"address"`
        Healthy bool   `json:"healthy"`
        Checked string `json:"lastChecked"`
    }{
        ID:      server.ID,
        Address: server.String(),
        Healthy: server.Healthy,
        Checked: server.LastCheck.Format(time.RFC3339),
    }
}

func main() {
    srv := NewBackendServer("backend-1", "10.0.0.1", 8080)
    fmt.Println(srv.String())         // 10.0.0.1:8080 (promoted from Endpoint)
    fmt.Println(srv.IsAvailable())    // true

    srv.RecordFailure()
    srv.RecordFailure()
    fmt.Printf("Failures: %d, Available: %v\n", srv.Failures, srv.IsAvailable())

    payload := createHealthCheckPayload(srv)
    fmt.Printf("%+v\n", payload)
}
```

---

## 8. Interfaces — The Heart of Go

### 8.1 Interface Design & The io Package

```go
package main

import (
    "bufio"
    "bytes"
    "fmt"
    "io"
    "net"
    "strings"
    "time"
)

// Small interfaces are powerful — Go's standard library proves this
// io.Reader: just Read(p []byte) (n int, err error)
// io.Writer: just Write(p []byte) (n int, err error)
// io.Closer: just Close() error

// Define interfaces that describe behavior
type Dialer interface {
    Dial(network, address string) (net.Conn, error)
}

type Listener interface {
    Accept() (net.Conn, error)
    Close() error
    Addr() net.Addr
}

// Composing interfaces
type ReadWriter interface {
    io.Reader
    io.Writer
}

// Protocol handler interface — pluggable protocols
type ProtocolHandler interface {
    HandleConnection(conn net.Conn) error
    Protocol() string
    HealthCheck() error
}

// Load balancer interface
type LoadBalancer interface {
    SelectBackend(ctx interface{}) (string, error)
    AddBackend(addr string, weight int)
    RemoveBackend(addr string)
    Backends() []string
}

// Round-robin implementation
type RoundRobinLB struct {
    backends []string
    counter  uint64
}

func (r *RoundRobinLB) SelectBackend(_ interface{}) (string, error) {
    if len(r.backends) == 0 {
        return "", fmt.Errorf("no backends available")
    }
    // Atomic would be used here in real code
    idx := r.counter % uint64(len(r.backends))
    r.counter++
    return r.backends[idx], nil
}

func (r *RoundRobinLB) AddBackend(addr string, _ int) {
    r.backends = append(r.backends, addr)
}

func (r *RoundRobinLB) RemoveBackend(addr string) {
    for i, b := range r.backends {
        if b == addr {
            r.backends = append(r.backends[:i], r.backends[i+1:]...)
            return
        }
    }
}

func (r *RoundRobinLB) Backends() []string {
    result := make([]string, len(r.backends))
    copy(result, r.backends)
    return result
}

// Interface composition and implementation checking
var _ LoadBalancer = (*RoundRobinLB)(nil) // compile-time check

// io.Reader/Writer wrapping — fundamental pattern in networking
// ByteCounter wraps a net.Conn and counts bytes
type ByteCountingConn struct {
    net.Conn
    BytesRead    int64
    BytesWritten int64
}

func (b *ByteCountingConn) Read(p []byte) (int, error) {
    n, err := b.Conn.Read(p)
    b.BytesRead += int64(n)
    return n, err
}

func (b *ByteCountingConn) Write(p []byte) (int, error) {
    n, err := b.Conn.Write(p)
    b.BytesWritten += int64(n)
    return n, err
}

// Timeout-wrapping connection
type TimeoutConn struct {
    net.Conn
    timeout time.Duration
}

func (t *TimeoutConn) Read(b []byte) (int, error) {
    t.Conn.SetReadDeadline(time.Now().Add(t.timeout))
    return t.Conn.Read(b)
}

func (t *TimeoutConn) Write(b []byte) (int, error) {
    t.Conn.SetWriteDeadline(time.Now().Add(t.timeout))
    return t.Conn.Write(b)
}

// Empty interface and type assertions
func processPayload(payload interface{}) {
    switch v := payload.(type) {
    case []byte:
        fmt.Printf("Raw bytes: %d bytes\n", len(v))
    case string:
        fmt.Printf("String: %q\n", v)
    case io.Reader:
        data, _ := io.ReadAll(v)
        fmt.Printf("Reader: %d bytes\n", len(data))
    case net.Conn:
        fmt.Printf("Connection from %s\n", v.RemoteAddr())
    default:
        fmt.Printf("Unknown type: %T\n", v)
    }
}

func main() {
    // Interface composition
    var buf bytes.Buffer
    var rw io.ReadWriter = &buf
    
    // Writing
    fmt.Fprint(rw, "hello network")
    
    // Reading
    scanner := bufio.NewScanner(rw)
    for scanner.Scan() {
        fmt.Println(scanner.Text())
    }

    // Any type that satisfies io.Reader works with io functions
    processPayload([]byte{1, 2, 3})
    processPayload("192.168.1.1")
    processPayload(strings.NewReader("from a string reader"))

    lb := &RoundRobinLB{}
    lb.AddBackend("10.0.0.1:8080", 1)
    lb.AddBackend("10.0.0.2:8080", 1)
    lb.AddBackend("10.0.0.3:8080", 1)

    for i := 0; i < 6; i++ {
        backend, _ := lb.SelectBackend(nil)
        fmt.Printf("Request %d -> %s\n", i+1, backend)
    }
}
```

### 8.2 Interface Internals — nil Interface vs nil Pointer

```go
package main

import "fmt"

type Error interface {
    Error() string
}

type NetworkError struct {
    Code    int
    Message string
}

func (e *NetworkError) Error() string {
    return fmt.Sprintf("[%d] %s", e.Code, e.Message)
}

// CLASSIC BUG: returning typed nil from interface-returning function
func badFunction() error {
    var err *NetworkError = nil // typed nil pointer
    // This looks like nil, but...
    return err // returns interface{type=*NetworkError, value=nil}
    // The interface is NOT nil! It has a type!
}

func goodFunction() error {
    // Explicitly return untyped nil when there's no error
    return nil
}

func main() {
    err := badFunction()
    if err != nil { // This evaluates to TRUE — the bug!
        fmt.Println("Bug: returned typed nil, but interface is not nil")
        fmt.Printf("Type: %T, Value: %v\n", err, err)
    }

    err2 := goodFunction()
    if err2 == nil {
        fmt.Println("Correct: genuine nil interface")
    }
}
```

---

## 9. Error Handling — Production Patterns

### 9.1 Error Types and Wrapping

```go
package main

import (
    "errors"
    "fmt"
    "net"
    "os"
    "syscall"
)

// Custom error types — provide context
type ConnectionError struct {
    Op      string // "connect", "read", "write"
    Network string // "tcp", "udp"
    Addr    string // "10.0.0.1:8080"
    Err     error  // underlying error
}

func (e *ConnectionError) Error() string {
    return fmt.Sprintf("%s %s %s: %v", e.Op, e.Network, e.Addr, e.Err)
}

// Unwrap — enables errors.Is/As chaining
func (e *ConnectionError) Unwrap() error {
    return e.Err
}

// Sentinel errors — for comparison
var (
    ErrConnectionRefused = errors.New("connection refused")
    ErrTimeout           = errors.New("connection timeout")
    ErrTLSHandshake      = errors.New("TLS handshake failed")
    ErrRateLimited       = errors.New("rate limited")
    ErrNoBackends        = errors.New("no available backends")
)

// Error wrapping with %w
func connectToBackend(addr string) error {
    conn, err := net.Dial("tcp", addr)
    if err != nil {
        // Wrap with context
        return fmt.Errorf("connectToBackend %s: %w", addr, err)
    }
    conn.Close()
    return nil
}

// errors.Is — checks error chain for a specific sentinel
func handleError(err error) {
    // Check if it's a specific error anywhere in the chain
    if errors.Is(err, os.ErrDeadlineExceeded) {
        fmt.Println("Timeout — retry with backoff")
        return
    }

    // Check for syscall errors
    if errors.Is(err, syscall.ECONNREFUSED) {
        fmt.Println("Connection refused — backend down")
        return
    }

    // errors.As — extract a specific error type from the chain
    var netErr *net.OpError
    if errors.As(err, &netErr) {
        fmt.Printf("Net error: op=%s, addr=%v\n", netErr.Op, netErr.Addr)

        var syscallErr *os.SyscallError
        if errors.As(err, &syscallErr) {
            fmt.Printf("Syscall: %s\n", syscallErr.Syscall)
        }
        return
    }

    var connErr *ConnectionError
    if errors.As(err, &connErr) {
        fmt.Printf("Connection error on %s: %v\n", connErr.Addr, connErr.Err)
        return
    }

    fmt.Printf("Unknown error: %v\n", err)
}

// Multiple error handling — joining errors
func validateEndpoints(endpoints []string) error {
    var errs []error
    for _, ep := range endpoints {
        if _, err := net.ResolveTCPAddr("tcp", ep); err != nil {
            errs = append(errs, fmt.Errorf("invalid endpoint %q: %w", ep, err))
        }
    }
    return errors.Join(errs...) // Go 1.20+ — joins all errors
}

// Retry with error inspection
func retryableError(err error) bool {
    if err == nil {
        return false
    }
    var netErr *net.OpError
    if errors.As(err, &netErr) {
        return netErr.Temporary() || netErr.Timeout()
    }
    return errors.Is(err, syscall.EAGAIN) || errors.Is(err, syscall.ETIMEDOUT)
}

func main() {
    err := connectToBackend("localhost:9999")
    if err != nil {
        handleError(err)
        fmt.Printf("Full error: %v\n", err)
        fmt.Printf("Retryable: %v\n", retryableError(err))
    }

    endpoints := []string{"10.0.0.1:8080", "invalid-addr", "10.0.0.2:not-a-port"}
    if err := validateEndpoints(endpoints); err != nil {
        fmt.Println("Validation errors:")
        fmt.Println(err)
    }
}
```

---

## 10. Defer, Panic & Recover

### 10.1 Defer — Guaranteed Cleanup

```go
package main

import (
    "fmt"
    "net"
    "os"
    "sync"
    "time"
)

// defer runs in LIFO order, after the surrounding function returns
// MOST IMPORTANT use: resource cleanup

func handleConnection(conn net.Conn) {
    defer conn.Close() // ALWAYS the first thing after getting a resource

    // Set deadline
    conn.SetDeadline(time.Now().Add(30 * time.Second))
    
    // Multiple defers — LIFO order
    defer fmt.Println("3: connection cleanup done")
    defer fmt.Printf("2: closed connection from %s\n", conn.RemoteAddr())
    defer fmt.Println("1: starting cleanup")

    // ... handle connection
}

func openAndProcessFile(name string) error {
    f, err := os.Open(name)
    if err != nil {
        return fmt.Errorf("open %s: %w", err)
    }
    defer f.Close() // guaranteed close regardless of path

    // Process file...
    return nil
}

// Defer with named return values — modifying return
func acquireLock(mu *sync.Mutex) (err error) {
    defer func() {
        if err != nil {
            mu.Unlock() // if something failed after locking, unlock
        }
    }()

    mu.Lock()
    // ... setup work that might fail
    return nil
}

// Defer captures variables by reference — loop defer gotcha
func dontDoThis() {
    files := []string{"a.txt", "b.txt", "c.txt"}
    for _, file := range files {
        f, err := os.Open(file)
        if err != nil {
            continue
        }
        defer f.Close() // BUG: all closes happen when function returns, not each iteration
        // For loop body here
    }
}

func doThisInstead() {
    files := []string{"a.txt", "b.txt", "c.txt"}
    for _, file := range files {
        func() {
            f, err := os.Open(file)
            if err != nil {
                return
            }
            defer f.Close() // now closes at end of anonymous function
            // process f
        }()
    }
}

// Panic & Recover — for truly exceptional situations
func safeHandler(conn net.Conn) {
    defer func() {
        if r := recover(); r != nil {
            fmt.Printf("Recovered from panic handling %s: %v\n", 
                conn.RemoteAddr(), r)
            conn.Close()
        }
    }()

    // Handler code that might panic
    processConnection(conn)
}

func processConnection(conn net.Conn) {
    buf := make([]byte, 4096)
    n, err := conn.Read(buf)
    if err != nil {
        panic(fmt.Sprintf("read failed: %v", err)) // Don't actually do this
    }
    _ = buf[:n]
}

// Server wrapper that recovers from panics in handlers
func serveWithRecovery(listener net.Listener, handler func(net.Conn)) {
    for {
        conn, err := listener.Accept()
        if err != nil {
            fmt.Printf("Accept error: %v\n", err)
            return
        }
        go func(c net.Conn) {
            defer func() {
                if r := recover(); r != nil {
                    fmt.Printf("Handler panicked: %v\n", r)
                }
                c.Close()
            }()
            handler(c)
        }(conn)
    }
}

func main() {
    fmt.Println("Defer, Panic & Recover examples")
}
```

---

## 11. Packages, Modules & Dependency Management

### 11.1 Module System

```go
// go.mod
module github.com/myorg/mynetworkproject

go 1.22

require (
    github.com/cilium/cilium v1.15.0
    google.golang.org/grpc v1.62.0
    google.golang.org/protobuf v1.33.0
    k8s.io/client-go v0.29.2
    k8s.io/apimachinery v0.29.2
    github.com/vishvananda/netlink v1.1.0
    github.com/containernetworking/cni v1.1.2
    go.uber.org/zap v1.27.0
    github.com/prometheus/client_golang v1.19.0
    golang.org/x/net v0.22.0
    golang.org/x/sys v0.18.0
)
```

```go
// Package declaration — every file must have this
package networking

// Package naming rules:
// - lowercase, single word
// - no underscores
// - match directory name
// - meaningful: packet, proxy, resolver, healthcheck

// Internal packages — only importable within the module
// internal/dataplane — cannot be imported by external modules

// Exported identifiers start with capital letter
// Unexported identifiers start with lowercase

package networking

// Exported type
type Resolver struct {
    servers []string // unexported field
    timeout int      // unexported field
}

// Exported constructor (Go convention: New*)
func NewResolver(servers []string) *Resolver {
    return &Resolver{
        servers: servers,
        timeout: 5,
    }
}

// Exported method
func (r *Resolver) Resolve(host string) (string, error) {
    // implementation
    return "", nil
}

// Unexported helper
func (r *Resolver) dialServer(server string) error {
    return nil
}
```

```bash
# Useful module commands
go mod graph                   # Show dependency graph
go mod why github.com/some/pkg # Why is this dependency needed?
go mod vendor                  # Copy dependencies to ./vendor
go list -m all                 # List all dependencies
go get -u ./...                # Update all dependencies
go get github.com/pkg@latest   # Update specific package

# Replace directive — useful for local development
# In go.mod:
# replace github.com/myorg/mylib => ../mylib
```

---

## 12. Goroutines — Concurrency Model

### 12.1 Goroutines in Depth

```go
package main

import (
    "fmt"
    "net"
    "runtime"
    "sync"
    "time"
)

// Goroutines are NOT threads — they are multiplexed on OS threads by the Go scheduler
// Go uses M:N threading: M goroutines on N OS threads
// A goroutine starts with 2KB stack, grows automatically up to 1GB (default)

func main() {
    // GOMAXPROCS — number of OS threads for goroutine scheduling
    // Default: number of CPUs
    procs := runtime.GOMAXPROCS(0) // 0 = query, don't change
    fmt.Printf("Using %d processors\n", procs)

    // Current goroutine count
    fmt.Printf("Active goroutines: %d\n", runtime.NumGoroutine())

    // Simple goroutine launch
    go func() {
        fmt.Println("Running in goroutine")
    }()

    // Goroutine with WaitGroup
    var wg sync.WaitGroup
    for i := 0; i < 5; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            fmt.Printf("Worker %d done\n", id)
        }(i) // Pass i as argument — avoid closure capture bug
    }
    wg.Wait()
}

// Worker pool — fundamental pattern for connection handling
type WorkerPool struct {
    tasks   chan func()
    wg      sync.WaitGroup
    once    sync.Once
    quit    chan struct{}
}

func NewWorkerPool(size int) *WorkerPool {
    p := &WorkerPool{
        tasks: make(chan func(), size*10),
        quit:  make(chan struct{}),
    }
    for i := 0; i < size; i++ {
        p.wg.Add(1)
        go p.worker()
    }
    return p
}

func (p *WorkerPool) worker() {
    defer p.wg.Done()
    for {
        select {
        case task, ok := <-p.tasks:
            if !ok {
                return
            }
            task()
        case <-p.quit:
            return
        }
    }
}

func (p *WorkerPool) Submit(task func()) {
    select {
    case p.tasks <- task:
    case <-p.quit:
        return
    }
}

func (p *WorkerPool) Stop() {
    p.once.Do(func() {
        close(p.quit)
        p.wg.Wait()
    })
}

// Goroutine-per-connection server — the classic Go pattern
func RunServer(addr string) error {
    listener, err := net.Listen("tcp", addr)
    if err != nil {
        return fmt.Errorf("listen on %s: %w", addr, err)
    }
    defer listener.Close()

    fmt.Printf("Listening on %s\n", addr)

    for {
        conn, err := listener.Accept()
        if err != nil {
            // Check if listener was closed
            select {
            default:
                fmt.Printf("Accept error: %v\n", err)
                continue
            }
        }
        go handleConn(conn) // Each connection gets its own goroutine
    }
}

func handleConn(conn net.Conn) {
    defer conn.Close()
    
    conn.SetDeadline(time.Now().Add(30 * time.Second))
    
    buf := make([]byte, 4096)
    for {
        n, err := conn.Read(buf)
        if err != nil {
            return // connection closed or error
        }
        
        // Echo back
        if _, err := conn.Write(buf[:n]); err != nil {
            return
        }
    }
}

// Goroutine leak prevention — CRITICAL in production
func leakExample(done <-chan struct{}) {
    go func() {
        for {
            select {
            case <-done: // ALWAYS provide a way to stop
                return
            default:
                // do work
                time.Sleep(time.Millisecond)
            }
        }
    }()
}
```

---

## 13. Channels — Communication Primitives

### 13.1 Channels — Complete Guide

```go
package main

import (
    "fmt"
    "net"
    "time"
)

func main() {
    // Unbuffered channel — synchronous, sender blocks until receiver is ready
    unbuffered := make(chan []byte)

    // Buffered channel — asynchronous up to buffer capacity
    buffered := make(chan []byte, 100)

    // Directional channels
    var sendOnly chan<- []byte = buffered  // can only send
    var recvOnly <-chan []byte = buffered  // can only receive

    _ = unbuffered
    _ = sendOnly
    _ = recvOnly

    // Channel operations
    ch := make(chan int, 3)
    ch <- 1    // send
    ch <- 2
    ch <- 3
    
    v1 := <-ch // receive
    v2, ok := <-ch // receive with existence check
    fmt.Println(v1, v2, ok)

    // Close channel — signals no more values
    close(ch)
    v3, ok := <-ch
    fmt.Println(v3, ok) // 3, true (last buffered value)
    v4, ok := <-ch
    fmt.Println(v4, ok) // 0, false (channel closed)
}

// Pipeline pattern — data flows through stages
func generatePackets(done <-chan struct{}) <-chan []byte {
    out := make(chan []byte, 10)
    go func() {
        defer close(out)
        for i := 0; i < 100; i++ {
            pkt := make([]byte, 64)
            pkt[0] = byte(i)
            select {
            case out <- pkt:
            case <-done:
                return
            }
        }
    }()
    return out
}

func filterPackets(done <-chan struct{}, in <-chan []byte) <-chan []byte {
    out := make(chan []byte, 10)
    go func() {
        defer close(out)
        for pkt := range in {
            if pkt[0]%2 == 0 { // only even packets
                select {
                case out <- pkt:
                case <-done:
                    return
                }
            }
        }
    }()
    return out
}

// Fan-out — distribute work to multiple workers
func fanOut(done <-chan struct{}, in <-chan []byte, workers int) []<-chan []byte {
    channels := make([]<-chan []byte, workers)
    for i := 0; i < workers; i++ {
        ch := make(chan []byte, 10)
        channels[i] = ch
        go func(out chan<- []byte) {
            defer close(out)
            for {
                select {
                case pkt, ok := <-in:
                    if !ok {
                        return
                    }
                    out <- pkt
                case <-done:
                    return
                }
            }
        }(ch)
    }
    return channels
}

// Fan-in — merge multiple channels into one
func fanIn(done <-chan struct{}, channels ...<-chan []byte) <-chan []byte {
    out := make(chan []byte, 100)
    var wg sync.WaitGroup

    merge := func(ch <-chan []byte) {
        defer wg.Done()
        for pkt := range ch {
            select {
            case out <- pkt:
            case <-done:
                return
            }
        }
    }

    wg.Add(len(channels))
    for _, ch := range channels {
        go merge(ch)
    }

    go func() {
        wg.Wait()
        close(out)
    }()

    return out
}

// Connection acceptor with channel-based dispatch
type ConnRouter struct {
    listener  net.Listener
    httpConns chan net.Conn
    grpcConns chan net.Conn
    quit      chan struct{}
}

func NewConnRouter(addr string) (*ConnRouter, error) {
    l, err := net.Listen("tcp", addr)
    if err != nil {
        return nil, err
    }
    return &ConnRouter{
        listener:  l,
        httpConns: make(chan net.Conn, 100),
        grpcConns: make(chan net.Conn, 100),
        quit:      make(chan struct{}),
    }, nil
}

func (r *ConnRouter) Start() {
    go func() {
        for {
            conn, err := r.listener.Accept()
            if err != nil {
                return
            }
            go r.route(conn)
        }
    }()
}

func (r *ConnRouter) route(conn net.Conn) {
    // Peek at first bytes to determine protocol
    buf := make([]byte, 5)
    conn.SetReadDeadline(time.Now().Add(5 * time.Second))
    n, err := conn.Read(buf[:])
    if err != nil {
        conn.Close()
        return
    }
    conn.SetReadDeadline(time.Time{}) // clear deadline

    // gRPC starts with "PRI " (HTTP/2 preface)
    if n >= 4 && string(buf[:4]) == "PRI " {
        r.grpcConns <- &prefixedConn{Conn: conn, prefix: buf[:n]}
    } else {
        r.httpConns <- &prefixedConn{Conn: conn, prefix: buf[:n]}
    }
}

// prefixedConn wraps a connection and prepends already-read bytes
type prefixedConn struct {
    net.Conn
    prefix []byte
    read   bool
}

func (p *prefixedConn) Read(b []byte) (int, error) {
    if !p.read && len(p.prefix) > 0 {
        n := copy(b, p.prefix)
        p.prefix = p.prefix[n:]
        if len(p.prefix) == 0 {
            p.read = true
        }
        return n, nil
    }
    return p.Conn.Read(b)
}

import "sync"
```

---

## 14. The `select` Statement

### 14.1 select — Multiplexing Channels

```go
package main

import (
    "context"
    "fmt"
    "net"
    "time"
)

func main() {
    ch1 := make(chan string, 1)
    ch2 := make(chan string, 1)

    go func() {
        time.Sleep(10 * time.Millisecond)
        ch1 <- "packet from ch1"
    }()
    go func() {
        time.Sleep(5 * time.Millisecond)
        ch2 <- "packet from ch2"
    }()

    // select blocks until one case is ready
    // If multiple are ready, one is chosen at random (fair)
    for i := 0; i < 2; i++ {
        select {
        case msg := <-ch1:
            fmt.Println("ch1:", msg)
        case msg := <-ch2:
            fmt.Println("ch2:", msg)
        }
    }

    // Non-blocking select with default
    ch3 := make(chan []byte, 1)
    select {
    case pkt := <-ch3:
        fmt.Println("Got packet:", pkt)
    default:
        fmt.Println("No packet available, continuing")
    }
}

// Timeout using select
func dialWithTimeout(network, addr string, timeout time.Duration) (net.Conn, error) {
    type result struct {
        conn net.Conn
        err  error
    }
    ch := make(chan result, 1)

    go func() {
        conn, err := net.Dial(network, addr)
        ch <- result{conn, err}
    }()

    select {
    case res := <-ch:
        return res.conn, res.err
    case <-time.After(timeout):
        return nil, fmt.Errorf("dial %s timeout after %v", addr, timeout)
    }
}

// Graceful shutdown pattern
func runServer(ctx context.Context, listener net.Listener) error {
    connCh := make(chan net.Conn, 100)
    errCh := make(chan error, 1)

    // Acceptor goroutine
    go func() {
        for {
            conn, err := listener.Accept()
            if err != nil {
                errCh <- err
                return
            }
            connCh <- conn
        }
    }()

    for {
        select {
        case <-ctx.Done():
            // Graceful shutdown
            listener.Close()
            fmt.Println("Server shutting down:", ctx.Err())
            return ctx.Err()

        case err := <-errCh:
            return fmt.Errorf("accept failed: %w", err)

        case conn := <-connCh:
            go func(c net.Conn) {
                defer c.Close()
                // handle connection
            }(conn)
        }
    }
}

// Priority channel pattern — process high-priority traffic first
func priorityProcessor(
    high <-chan []byte,
    low <-chan []byte,
    done <-chan struct{},
) {
    for {
        // First select — drain high priority
        select {
        case pkt := <-high:
            fmt.Println("Processing high-priority:", len(pkt))
            continue
        default:
        }

        // Second select — process either
        select {
        case pkt := <-high:
            fmt.Println("Processing high-priority:", len(pkt))
        case pkt := <-low:
            fmt.Println("Processing low-priority:", len(pkt))
        case <-done:
            return
        }
    }
}

// Heartbeat pattern
func withHeartbeat(
    done <-chan struct{},
    interval time.Duration,
    work func() error,
) <-chan error {
    errCh := make(chan error, 1)
    heartbeat := make(chan struct{}, 1)

    go func() {
        defer close(errCh)
        ticker := time.NewTicker(interval)
        defer ticker.Stop()

        for {
            select {
            case <-ticker.C:
                heartbeat <- struct{}{}
                if err := work(); err != nil {
                    errCh <- err
                    return
                }
            case <-done:
                return
            }
        }
    }()

    go func() {
        for range heartbeat {
            fmt.Println("Heartbeat")
        }
    }()

    return errCh
}

func main() {}
```

---

## 15. Sync Package — Synchronization Primitives

### 15.1 Mutex, RWMutex, WaitGroup, Once, Cond

```go
package main

import (
    "fmt"
    "sync"
    "sync/atomic"
    "time"
)

// sync.Mutex — mutual exclusion
type ConnectionPool struct {
    mu          sync.Mutex
    connections map[string][]interface{} // addr -> pool of connections
    maxPerAddr  int
}

func (p *ConnectionPool) Get(addr string) (interface{}, bool) {
    p.mu.Lock()
    defer p.mu.Unlock()
    
    conns := p.connections[addr]
    if len(conns) == 0 {
        return nil, false
    }
    
    conn := conns[len(conns)-1]
    p.connections[addr] = conns[:len(conns)-1]
    return conn, true
}

func (p *ConnectionPool) Put(addr string, conn interface{}) {
    p.mu.Lock()
    defer p.mu.Unlock()
    
    if len(p.connections[addr]) < p.maxPerAddr {
        p.connections[addr] = append(p.connections[addr], conn)
    }
    // else: drop the connection (close it in real code)
}

// sync.RWMutex — multiple readers, single writer
type DNSCache struct {
    mu      sync.RWMutex
    entries map[string]cacheEntry
}

type cacheEntry struct {
    ip      string
    expires time.Time
}

func (c *DNSCache) Lookup(host string) (string, bool) {
    c.mu.RLock() // Multiple goroutines can read simultaneously
    defer c.mu.RUnlock()
    
    entry, ok := c.entries[host]
    if !ok || time.Now().After(entry.expires) {
        return "", false
    }
    return entry.ip, true
}

func (c *DNSCache) Set(host, ip string, ttl time.Duration) {
    c.mu.Lock() // Exclusive write lock
    defer c.mu.Unlock()
    
    c.entries[host] = cacheEntry{
        ip:      ip,
        expires: time.Now().Add(ttl),
    }
}

// sync.WaitGroup — wait for goroutine completion
func processPacketsBatch(packets [][]byte) error {
    var (
        wg   sync.WaitGroup
        mu   sync.Mutex
        errs []error
    )

    for _, pkt := range packets {
        wg.Add(1)
        go func(p []byte) {
            defer wg.Done()
            if err := processPacket(p); err != nil {
                mu.Lock()
                errs = append(errs, err)
                mu.Unlock()
            }
        }(pkt)
    }

    wg.Wait()
    if len(errs) > 0 {
        return fmt.Errorf("batch processing had %d errors", len(errs))
    }
    return nil
}

func processPacket(pkt []byte) error {
    _ = pkt
    return nil
}

// sync.Once — guaranteed single initialization
type ServiceDiscovery struct {
    once      sync.Once
    client    interface{}
    initErr   error
    endpoints []string
}

func (s *ServiceDiscovery) Client() (interface{}, error) {
    s.once.Do(func() {
        // Expensive initialization — runs exactly once
        fmt.Println("Initializing service discovery client")
        // s.client, s.initErr = newClient(...)
    })
    return s.client, s.initErr
}

// sync/atomic — lock-free operations for counters and flags
type NetworkStats struct {
    PacketsRx   atomic.Uint64
    PacketsTx   atomic.Uint64
    BytesRx     atomic.Uint64
    BytesTx     atomic.Uint64
    ActiveConns atomic.Int64
    Errors      atomic.Uint64
}

func (s *NetworkStats) RecordRx(bytes int) {
    s.PacketsRx.Add(1)
    s.BytesRx.Add(uint64(bytes))
}

func (s *NetworkStats) RecordTx(bytes int) {
    s.PacketsTx.Add(1)
    s.BytesTx.Add(uint64(bytes))
}

func (s *NetworkStats) ConnectionOpened() {
    s.ActiveConns.Add(1)
}

func (s *NetworkStats) ConnectionClosed() {
    s.ActiveConns.Add(-1)
}

// sync.Cond — conditional variable for complex signaling
type PacketQueue struct {
    mu      sync.Mutex
    cond    *sync.Cond
    packets [][]byte
    closed  bool
    maxSize int
}

func NewPacketQueue(maxSize int) *PacketQueue {
    q := &PacketQueue{maxSize: maxSize}
    q.cond = sync.NewCond(&q.mu)
    return q
}

func (q *PacketQueue) Enqueue(pkt []byte) error {
    q.mu.Lock()
    defer q.mu.Unlock()
    
    for len(q.packets) >= q.maxSize && !q.closed {
        q.cond.Wait() // releases lock, waits for signal
    }
    
    if q.closed {
        return fmt.Errorf("queue closed")
    }
    
    q.packets = append(q.packets, pkt)
    q.cond.Signal() // wake one waiter
    return nil
}

func (q *PacketQueue) Dequeue() ([]byte, bool) {
    q.mu.Lock()
    defer q.mu.Unlock()
    
    for len(q.packets) == 0 && !q.closed {
        q.cond.Wait()
    }
    
    if len(q.packets) == 0 {
        return nil, false // closed and empty
    }
    
    pkt := q.packets[0]
    q.packets = q.packets[1:]
    q.cond.Signal() // wake one producer
    return pkt, true
}

func (q *PacketQueue) Close() {
    q.mu.Lock()
    defer q.mu.Unlock()
    q.closed = true
    q.cond.Broadcast() // wake ALL waiters
}

func main() {
    stats := &NetworkStats{}
    stats.RecordRx(1500)
    stats.RecordTx(64)
    stats.ConnectionOpened()
    
    fmt.Printf("Packets RX: %d, TX: %d\n", stats.PacketsRx.Load(), stats.PacketsTx.Load())
    fmt.Printf("Active connections: %d\n", stats.ActiveConns.Load())
}
```

---

## 16. Context Package — Cancellation & Deadlines

### 16.1 Context — Mandatory in All Network Code

```go
package main

import (
    "context"
    "fmt"
    "net"
    "net/http"
    "time"
)

// context.Context is THE standard way to propagate:
// 1. Cancellation signals
// 2. Deadlines and timeouts
// 3. Request-scoped values (trace IDs, auth tokens)

// RULE: context is always the FIRST parameter
// RULE: Never store context in a struct
// RULE: Always propagate context down the call chain

func main() {
    // Background — the root context, never cancelled
    bg := context.Background()

    // TODO — placeholder, should be replaced
    // todo := context.TODO()

    // WithCancel — manual cancellation
    ctx, cancel := context.WithCancel(bg)
    defer cancel() // ALWAYS defer cancel to prevent goroutine leaks

    go worker(ctx)
    time.Sleep(50 * time.Millisecond)
    cancel() // signal worker to stop
    time.Sleep(10 * time.Millisecond)

    // WithTimeout — automatic cancellation after duration
    dialCtx, dialCancel := context.WithTimeout(bg, 5*time.Second)
    defer dialCancel()

    conn, err := (&net.Dialer{}).DialContext(dialCtx, "tcp", "example.com:80")
    if err != nil {
        fmt.Println("Dial failed:", err)
    } else {
        conn.Close()
    }

    // WithDeadline — cancel at specific time
    deadline := time.Now().Add(10 * time.Second)
    deadlineCtx, deadlineCancel := context.WithDeadline(bg, deadline)
    defer deadlineCancel()

    fmt.Println("Deadline:", deadlineCtx.Deadline())

    // WithValue — attach request-scoped data
    type contextKey string
    const (
        keyTraceID   contextKey = "traceID"
        keyRequestID contextKey = "requestID"
    )

    requestCtx := context.WithValue(bg, keyTraceID, "abc-123")
    requestCtx = context.WithValue(requestCtx, keyRequestID, "req-456")

    handleRequest(requestCtx)
}

func worker(ctx context.Context) {
    ticker := time.NewTicker(10 * time.Millisecond)
    defer ticker.Stop()
    
    for {
        select {
        case <-ctx.Done():
            fmt.Println("Worker stopped:", ctx.Err())
            return
        case <-ticker.C:
            fmt.Println("Worker tick")
        }
    }
}

type contextKey string

const keyTraceID contextKey = "traceID"

func handleRequest(ctx context.Context) {
    traceID, _ := ctx.Value(keyTraceID).(string)
    fmt.Printf("Handling request with traceID: %s\n", traceID)

    // Pass context to all downstream calls
    fetchData(ctx)
}

func fetchData(ctx context.Context) {
    req, _ := http.NewRequestWithContext(ctx, "GET", "http://example.com", nil)
    client := &http.Client{Timeout: 5 * time.Second}
    resp, err := client.Do(req)
    if err != nil {
        if ctx.Err() != nil {
            fmt.Println("Request cancelled:", ctx.Err())
        } else {
            fmt.Println("Request failed:", err)
        }
        return
    }
    defer resp.Body.Close()
    fmt.Println("Response:", resp.Status)
}

// Propagating context through your networking stack
type Proxy struct {
    dialer  *net.Dialer
    timeout time.Duration
}

func (p *Proxy) Forward(ctx context.Context, conn net.Conn, target string) error {
    // Create a child context with timeout for the upstream connection
    dialCtx, cancel := context.WithTimeout(ctx, p.timeout)
    defer cancel()

    upstream, err := p.dialer.DialContext(dialCtx, "tcp", target)
    if err != nil {
        return fmt.Errorf("dial upstream %s: %w", target, err)
    }
    defer upstream.Close()

    // Bidirectional copy with context cancellation
    errCh := make(chan error, 2)

    go func() {
        _, err := copyWithContext(ctx, upstream, conn)
        errCh <- err
    }()

    go func() {
        _, err := copyWithContext(ctx, conn, upstream)
        errCh <- err
    }()

    select {
    case err := <-errCh:
        return err
    case <-ctx.Done():
        return ctx.Err()
    }
}

func copyWithContext(ctx context.Context, dst, src net.Conn) (int64, error) {
    buf := make([]byte, 32*1024)
    var total int64
    for {
        select {
        case <-ctx.Done():
            return total, ctx.Err()
        default:
        }
        src.SetReadDeadline(time.Now().Add(100 * time.Millisecond))
        n, err := src.Read(buf)
        if n > 0 {
            written, werr := dst.Write(buf[:n])
            total += int64(written)
            if werr != nil {
                return total, werr
            }
        }
        if err != nil {
            return total, err
        }
    }
}
```

---

## 17. The `net` Package — Low-Level Networking

### 17.1 TCP — Complete Implementation

```go
package main

import (
    "bufio"
    "context"
    "fmt"
    "io"
    "net"
    "sync"
    "time"
)

// TCP Server with all production features
type TCPServer struct {
    addr     string
    listener net.Listener
    handler  func(context.Context, net.Conn)
    
    // Graceful shutdown
    ctx    context.Context
    cancel context.CancelFunc
    wg     sync.WaitGroup
    
    // Configuration
    readTimeout  time.Duration
    writeTimeout time.Duration
    maxConns     int
    
    // Semaphore for connection limiting
    connSem chan struct{}
}

func NewTCPServer(addr string, maxConns int) *TCPServer {
    ctx, cancel := context.WithCancel(context.Background())
    return &TCPServer{
        addr:         addr,
        ctx:          ctx,
        cancel:       cancel,
        readTimeout:  30 * time.Second,
        writeTimeout: 30 * time.Second,
        maxConns:     maxConns,
        connSem:      make(chan struct{}, maxConns),
    }
}

func (s *TCPServer) Start(handler func(context.Context, net.Conn)) error {
    lc := net.ListenConfig{
        KeepAlive: 30 * time.Second,
        Control: func(network, address string, c syscall.RawConn) error {
            // Set SO_REUSEPORT, TCP_FASTOPEN, etc.
            return nil
        },
    }

    l, err := lc.Listen(s.ctx, "tcp", s.addr)
    if err != nil {
        return fmt.Errorf("listen: %w", err)
    }
    s.listener = l
    s.handler = handler

    fmt.Printf("TCP server listening on %s\n", s.addr)

    s.wg.Add(1)
    go s.serve()
    return nil
}

func (s *TCPServer) serve() {
    defer s.wg.Done()

    for {
        // Acquire semaphore (blocks if at max connections)
        select {
        case s.connSem <- struct{}{}:
        case <-s.ctx.Done():
            return
        }

        conn, err := s.listener.Accept()
        if err != nil {
            <-s.connSem // release
            select {
            case <-s.ctx.Done():
                return // normal shutdown
            default:
                fmt.Printf("Accept error: %v\n", err)
                // Exponential backoff for transient errors
                time.Sleep(5 * time.Millisecond)
                continue
            }
        }

        s.wg.Add(1)
        go s.handleConnection(conn)
    }
}

func (s *TCPServer) handleConnection(conn net.Conn) {
    defer s.wg.Done()
    defer func() { <-s.connSem }() // release semaphore slot
    defer conn.Close()

    // Per-connection context — cancelled when server shuts down
    connCtx, connCancel := context.WithCancel(s.ctx)
    defer connCancel()

    // Ensure timeouts are enforced
    conn = &timedConn{
        Conn:         conn,
        readTimeout:  s.readTimeout,
        writeTimeout: s.writeTimeout,
    }

    s.handler(connCtx, conn)
}

func (s *TCPServer) Shutdown(ctx context.Context) error {
    s.cancel()
    s.listener.Close()

    done := make(chan struct{})
    go func() {
        s.wg.Wait()
        close(done)
    }()

    select {
    case <-done:
        fmt.Println("Server shutdown complete")
        return nil
    case <-ctx.Done():
        return fmt.Errorf("shutdown timed out: %w", ctx.Err())
    }
}

type timedConn struct {
    net.Conn
    readTimeout  time.Duration
    writeTimeout time.Duration
}

func (t *timedConn) Read(b []byte) (int, error) {
    if t.readTimeout > 0 {
        t.Conn.SetReadDeadline(time.Now().Add(t.readTimeout))
    }
    return t.Conn.Read(b)
}

func (t *timedConn) Write(b []byte) (int, error) {
    if t.writeTimeout > 0 {
        t.Conn.SetWriteDeadline(time.Now().Add(t.writeTimeout))
    }
    return t.Conn.Write(b)
}

// TCP Client with retry and connection pooling
type TCPClient struct {
    dialer      *net.Dialer
    addr        string
    maxRetries  int
    retryDelay  time.Duration
}

func NewTCPClient(addr string) *TCPClient {
    return &TCPClient{
        dialer: &net.Dialer{
            Timeout:   10 * time.Second,
            KeepAlive: 30 * time.Second,
        },
        addr:        addr,
        maxRetries:  3,
        retryDelay:  500 * time.Millisecond,
    }
}

func (c *TCPClient) Connect(ctx context.Context) (net.Conn, error) {
    var (
        conn net.Conn
        err  error
    )

    for attempt := 0; attempt < c.maxRetries; attempt++ {
        if attempt > 0 {
            delay := c.retryDelay * time.Duration(1<<uint(attempt-1))
            select {
            case <-time.After(delay):
            case <-ctx.Done():
                return nil, ctx.Err()
            }
        }

        conn, err = c.dialer.DialContext(ctx, "tcp", c.addr)
        if err == nil {
            return conn, nil
        }

        if !isRetryableError(err) {
            return nil, fmt.Errorf("non-retryable error: %w", err)
        }

        fmt.Printf("Attempt %d failed: %v\n", attempt+1, err)
    }

    return nil, fmt.Errorf("failed after %d attempts: %w", c.maxRetries, err)
}

func isRetryableError(err error) bool {
    if err == nil {
        return false
    }
    netErr, ok := err.(net.Error)
    return ok && (netErr.Timeout() || netErr.Temporary())
}

// UDP Server — for DNS, metrics, etc.
func runUDPServer(ctx context.Context, addr string) error {
    conn, err := net.ListenPacket("udp", addr)
    if err != nil {
        return fmt.Errorf("UDP listen on %s: %w", addr, err)
    }
    defer conn.Close()

    fmt.Printf("UDP server on %s\n", addr)

    buf := make([]byte, 65535) // max UDP datagram size

    for {
        conn.SetReadDeadline(time.Now().Add(100 * time.Millisecond))
        n, remoteAddr, err := conn.ReadFrom(buf)
        if err != nil {
            if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
                select {
                case <-ctx.Done():
                    return nil
                default:
                    continue
                }
            }
            return fmt.Errorf("ReadFrom: %w", err)
        }

        go handleUDP(conn, remoteAddr, buf[:n])
    }
}

func handleUDP(conn net.PacketConn, addr net.Addr, data []byte) {
    // Process and respond
    response := processUDPPacket(data)
    conn.WriteTo(response, addr)
}

func processUDPPacket(data []byte) []byte {
    return data // echo
}

// Unix Domain Socket — for inter-process communication on same host
func unixSocketExample() {
    const socketPath = "/tmp/myservice.sock"

    // Server
    l, _ := net.Listen("unix", socketPath)
    defer l.Close()

    go func() {
        conn, _ := l.Accept()
        defer conn.Close()
        
        scanner := bufio.NewScanner(conn)
        for scanner.Scan() {
            fmt.Fprintf(conn, "Echo: %s\n", scanner.Text())
        }
    }()

    // Client
    conn, _ := net.Dial("unix", socketPath)
    defer conn.Close()
    
    fmt.Fprintln(conn, "hello")
    
    buf := make([]byte, 64)
    n, _ := conn.Read(buf)
    fmt.Printf("Server said: %s", buf[:n])
}

// Network address parsing utilities
func networkExamples() {
    // Parse IP addresses
    ip4 := net.ParseIP("192.168.1.1")
    ip6 := net.ParseIP("2001:db8::1")
    
    fmt.Printf("IPv4: %v, is v4: %v\n", ip4, ip4.To4() != nil)
    fmt.Printf("IPv6: %v, is v6: %v\n", ip6, ip6.To4() == nil)

    // Parse CIDR
    _, network, _ := net.ParseCIDR("10.0.0.0/8")
    testIP := net.ParseIP("10.1.2.3")
    fmt.Printf("%v contains %v: %v\n", network, testIP, network.Contains(testIP))

    // Interface enumeration
    ifaces, _ := net.Interfaces()
    for _, iface := range ifaces {
        if iface.Flags&net.FlagUp == 0 {
            continue // skip down interfaces
        }
        addrs, _ := iface.Addrs()
        for _, addr := range addrs {
            fmt.Printf("%s: %s\n", iface.Name, addr)
        }
    }

    // DNS resolution
    ips, _ := net.LookupHost("google.com")
    fmt.Println("google.com IPs:", ips)

    cname, _ := net.LookupCNAME("www.google.com")
    fmt.Println("CNAME:", cname)

    // Reverse DNS
    names, _ := net.LookupAddr("8.8.8.8")
    fmt.Println("8.8.8.8 PTR:", names)
}

import "syscall"

func main() {
    networkExamples()
    
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    go runUDPServer(ctx, "127.0.0.1:9999")

    server := NewTCPServer("127.0.0.1:8888", 100)
    server.Start(func(ctx context.Context, conn net.Conn) {
        io.Copy(conn, conn) // echo server
    })

    time.Sleep(100 * time.Millisecond)

    shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer shutdownCancel()
    server.Shutdown(shutdownCtx)
}
```

---

## 18. HTTP Client & Server (`net/http`)

### 18.1 Production HTTP Server

```go
package main

import (
    "context"
    "encoding/json"
    "fmt"
    "io"
    "log"
    "net"
    "net/http"
    "net/http/httputil"
    "net/url"
    "time"
)

// HTTP Server with middleware chain
func NewHTTPServer(addr string) *http.Server {
    mux := http.NewServeMux()

    // Register routes
    mux.Handle("/healthz", handleHealth())
    mux.Handle("/ready", handleReady())
    mux.Handle("/metrics", handleMetrics())
    mux.Handle("/api/v1/", handleAPI())

    // Build middleware chain
    handler := chainMiddleware(
        mux,
        middlewareLogging,
        middlewareRecovery,
        middlewareTimeout(30*time.Second),
        middlewareRequestID,
    )

    return &http.Server{
        Addr:    addr,
        Handler: handler,

        // Production timeouts — CRITICAL
        ReadTimeout:       15 * time.Second,
        ReadHeaderTimeout: 5 * time.Second,
        WriteTimeout:      15 * time.Second,
        IdleTimeout:       120 * time.Second,

        // Connection management
        MaxHeaderBytes: 1 << 20, // 1MB

        // Custom error log
        ErrorLog: log.New(log.Writer(), "[HTTP] ", log.LstdFlags),

        // Base context for all requests
        BaseContext: func(l net.Listener) context.Context {
            return context.Background()
        },
    }
}

// Middleware type
type Middleware func(http.Handler) http.Handler

func chainMiddleware(h http.Handler, middlewares ...Middleware) http.Handler {
    // Apply in reverse so first middleware is outermost
    for i := len(middlewares) - 1; i >= 0; i-- {
        h = middlewares[i](h)
    }
    return h
}

func middlewareLogging(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        wrapped := &responseWriter{ResponseWriter: w, status: http.StatusOK}
        next.ServeHTTP(wrapped, r)
        log.Printf("%s %s %d %v %s",
            r.Method, r.URL.Path, wrapped.status,
            time.Since(start), r.RemoteAddr)
    })
}

type responseWriter struct {
    http.ResponseWriter
    status  int
    written int64
}

func (rw *responseWriter) WriteHeader(status int) {
    rw.status = status
    rw.ResponseWriter.WriteHeader(status)
}

func (rw *responseWriter) Write(b []byte) (int, error) {
    n, err := rw.ResponseWriter.Write(b)
    rw.written += int64(n)
    return n, err
}

func middlewareRecovery(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        defer func() {
            if rec := recover(); rec != nil {
                log.Printf("Panic: %v", rec)
                http.Error(w, "Internal Server Error", http.StatusInternalServerError)
            }
        }()
        next.ServeHTTP(w, r)
    })
}

func middlewareTimeout(d time.Duration) Middleware {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            ctx, cancel := context.WithTimeout(r.Context(), d)
            defer cancel()
            next.ServeHTTP(w, r.WithContext(ctx))
        })
    }
}

func middlewareRequestID(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        requestID := r.Header.Get("X-Request-ID")
        if requestID == "" {
            requestID = fmt.Sprintf("%d", time.Now().UnixNano())
        }
        w.Header().Set("X-Request-ID", requestID)
        ctx := context.WithValue(r.Context(), ctxKeyRequestID{}, requestID)
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

type ctxKeyRequestID struct{}

// Handler implementations
func handleHealth() http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.Header().Set("Content-Type", "application/json")
        json.NewEncoder(w).Encode(map[string]string{"status": "healthy"})
    })
}

func handleReady() http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Check dependencies
        w.WriteHeader(http.StatusOK)
        fmt.Fprint(w, "ready")
    })
}

func handleMetrics() http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprint(w, "# metrics here")
    })
}

func handleAPI() http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
    })
}

// HTTP Reverse Proxy — core of any API gateway
func newReverseProxy(targetURL string) (*httputil.ReverseProxy, error) {
    target, err := url.Parse(targetURL)
    if err != nil {
        return nil, err
    }

    proxy := httputil.NewSingleHostReverseProxy(target)

    // Custom director — modify upstream request
    originalDirector := proxy.Director
    proxy.Director = func(req *http.Request) {
        originalDirector(req)
        req.Header.Set("X-Forwarded-For", req.RemoteAddr)
        req.Header.Set("X-Forwarded-Proto", "https")
        req.Header.Del("X-Internal-Header")
    }

    // Custom transport with connection pooling
    proxy.Transport = &http.Transport{
        MaxIdleConns:          100,
        MaxIdleConnsPerHost:   10,
        MaxConnsPerHost:       100,
        IdleConnTimeout:       90 * time.Second,
        TLSHandshakeTimeout:   10 * time.Second,
        ExpectContinueTimeout: 1 * time.Second,
        DisableKeepAlives:     false,
        ForceAttemptHTTP2:     true,
    }

    // Custom error handler
    proxy.ErrorHandler = func(w http.ResponseWriter, r *http.Request, err error) {
        log.Printf("Proxy error: %v", err)
        if err == context.Canceled {
            w.WriteHeader(499) // Client closed request
            return
        }
        http.Error(w, "Bad Gateway", http.StatusBadGateway)
    }

    return proxy, nil
}

// HTTP Client — production-grade
func newHTTPClient() *http.Client {
    transport := &http.Transport{
        // Connection pooling
        MaxIdleConns:          200,
        MaxIdleConnsPerHost:   20,
        MaxConnsPerHost:       100,
        IdleConnTimeout:       90 * time.Second,
        
        // Timeouts
        TLSHandshakeTimeout:   10 * time.Second,
        ExpectContinueTimeout: 1 * time.Second,
        ResponseHeaderTimeout: 10 * time.Second,
        
        // TCP settings
        DialContext: (&net.Dialer{
            Timeout:   30 * time.Second,
            KeepAlive: 30 * time.Second,
        }).DialContext,

        // HTTP/2
        ForceAttemptHTTP2: true,
    }

    return &http.Client{
        Transport: transport,
        Timeout:   30 * time.Second,
        CheckRedirect: func(req *http.Request, via []*http.Request) error {
            if len(via) >= 3 {
                return fmt.Errorf("too many redirects")
            }
            return nil
        },
    }
}

func doRequest(ctx context.Context, client *http.Client, method, url string, body io.Reader) (*http.Response, error) {
    req, err := http.NewRequestWithContext(ctx, method, url, body)
    if err != nil {
        return nil, fmt.Errorf("create request: %w", err)
    }

    req.Header.Set("Content-Type", "application/json")
    req.Header.Set("Accept", "application/json")
    req.Header.Set("User-Agent", "mynetworkproxy/1.0")

    resp, err := client.Do(req)
    if err != nil {
        return nil, fmt.Errorf("do request: %w", err)
    }

    if resp.StatusCode >= 400 {
        body, _ := io.ReadAll(io.LimitReader(resp.Body, 1024))
        resp.Body.Close()
        return nil, fmt.Errorf("server returned %d: %s", resp.StatusCode, body)
    }

    return resp, nil
}

func main() {
    server := NewHTTPServer(":8080")
    
    go func() {
        if err := server.ListenAndServe(); err != http.ErrServerClosed {
            log.Fatal("Server error:", err)
        }
    }()

    time.Sleep(100 * time.Millisecond)

    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()
    
    if err := server.Shutdown(ctx); err != nil {
        log.Printf("Shutdown error: %v", err)
    }
}
```

---

## 19. TLS & Secure Communication

### 19.1 TLS Configuration

```go
package main

import (
    "crypto/tls"
    "crypto/x509"
    "fmt"
    "net"
    "net/http"
    "os"
    "time"
)

// TLS server with full configuration
func newTLSConfig(certFile, keyFile, caFile string) (*tls.Config, error) {
    cert, err := tls.LoadX509KeyPair(certFile, keyFile)
    if err != nil {
        return nil, fmt.Errorf("load key pair: %w", err)
    }

    // CA certificate pool for client authentication (mTLS)
    caCert, err := os.ReadFile(caFile)
    if err != nil {
        return nil, fmt.Errorf("read CA cert: %w", err)
    }

    caCertPool := x509.NewCertPool()
    if !caCertPool.AppendCertsFromPEM(caCert) {
        return nil, fmt.Errorf("failed to parse CA cert")
    }

    return &tls.Config{
        // Certificates
        Certificates: []tls.Certificate{cert},
        
        // Mutual TLS — verify client certificates
        ClientCAs:  caCertPool,
        ClientAuth: tls.RequireAndVerifyClientCert,

        // Minimum TLS version — never below 1.2
        MinVersion: tls.VersionTLS13,

        // Cipher suites — explicit list for TLS 1.2
        // TLS 1.3 ciphers are managed by Go automatically
        CipherSuites: []uint16{
            tls.TLS_AES_128_GCM_SHA256,        // TLS 1.3
            tls.TLS_AES_256_GCM_SHA384,        // TLS 1.3
            tls.TLS_CHACHA20_POLY1305_SHA256,  // TLS 1.3
            tls.TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,
            tls.TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
        },

        // Session tickets for resumption
        SessionTicketsDisabled: false,

        // Certificate verification
        VerifyPeerCertificate: func(rawCerts [][]byte, chains [][]*x509.Certificate) error {
            if len(chains) == 0 || len(chains[0]) == 0 {
                return fmt.Errorf("no certificate chain")
            }
            cert := chains[0][0]
            if time.Now().After(cert.NotAfter) {
                return fmt.Errorf("certificate expired")
            }
            return nil
        },

        // ALPN — negotiating protocols
        NextProtos: []string{"h2", "http/1.1"},
    }, nil
}

// TLS Client config (for connecting to secure services)
func newTLSClientConfig(caFile, certFile, keyFile string) (*tls.Config, error) {
    caCert, err := os.ReadFile(caFile)
    if err != nil {
        return nil, err
    }
    caCertPool := x509.NewCertPool()
    caCertPool.AppendCertsFromPEM(caCert)

    // Client certificate for mTLS
    cert, err := tls.LoadX509KeyPair(certFile, keyFile)
    if err != nil {
        return nil, err
    }

    return &tls.Config{
        RootCAs:      caCertPool,
        Certificates: []tls.Certificate{cert},
        MinVersion:   tls.VersionTLS13,
    }, nil
}

// TLS-enabled TCP server
func runTLSServer(addr, certFile, keyFile, caFile string) error {
    tlsConfig, err := newTLSConfig(certFile, keyFile, caFile)
    if err != nil {
        return err
    }

    listener, err := tls.Listen("tcp", addr, tlsConfig)
    if err != nil {
        return fmt.Errorf("TLS listen: %w", err)
    }
    defer listener.Close()

    fmt.Printf("TLS server on %s\n", addr)

    for {
        conn, err := listener.Accept()
        if err != nil {
            return err
        }
        go handleTLSConn(conn.(*tls.Conn))
    }
}

func handleTLSConn(conn *tls.Conn) {
    defer conn.Close()

    // Complete TLS handshake (optional — Accept already does this)
    if err := conn.Handshake(); err != nil {
        fmt.Printf("TLS handshake failed: %v\n", err)
        return
    }

    state := conn.ConnectionState()
    fmt.Printf("TLS version: %x\n", state.Version)
    fmt.Printf("Cipher suite: %x\n", state.CipherSuite)
    fmt.Printf("Server name: %s\n", state.ServerName)

    // Check peer certificate (if mTLS)
    if len(state.PeerCertificates) > 0 {
        cert := state.PeerCertificates[0]
        fmt.Printf("Client: %s\n", cert.Subject.CommonName)
    }
}

// In-memory TLS for testing (self-signed)
func generateSelfSignedConfig() *tls.Config {
    // Use crypto/rand and x509 to generate cert on the fly
    // This is common in tests and development
    config := &tls.Config{
        InsecureSkipVerify: true, // NEVER in production
    }
    return config
}

// HTTPS client with custom TLS
func newSecureHTTPClient(caFile, certFile, keyFile string) (*http.Client, error) {
    tlsConfig, err := newTLSClientConfig(caFile, certFile, keyFile)
    if err != nil {
        return nil, err
    }

    transport := &http.Transport{
        TLSClientConfig:     tlsConfig,
        MaxIdleConns:        100,
        MaxIdleConnsPerHost: 10,
        IdleConnTimeout:     90 * time.Second,
        ForceAttemptHTTP2:   true,
        DialContext: (&net.Dialer{
            Timeout:   10 * time.Second,
            KeepAlive: 30 * time.Second,
        }).DialContext,
    }

    return &http.Client{
        Transport: transport,
        Timeout:   30 * time.Second,
    }, nil
}

func main() {
    fmt.Println("TLS examples — needs actual cert files to run")
}
```

---

## 20. Encoding: JSON, Binary & Protocol Buffers

### 20.1 JSON Encoding/Decoding

```go
package main

import (
    "bytes"
    "encoding/binary"
    "encoding/json"
    "fmt"
    "io"
    "net"
)

// JSON for control plane / API communication
type ServiceConfig struct {
    Name      string            `json:"name"`
    Endpoints []EndpointConfig  `json:"endpoints"`
    LB        string            `json:"loadBalancing"`
    Timeout   int               `json:"timeoutMs"`
    Retry     *RetryConfig      `json:"retry,omitempty"`
    Labels    map[string]string `json:"labels,omitempty"`
}

type EndpointConfig struct {
    Address string `json:"address"`
    Port    int    `json:"port"`
    Weight  int    `json:"weight"`
}

type RetryConfig struct {
    MaxAttempts int `json:"maxAttempts"`
    BackoffMs   int `json:"backoffMs"`
}

func jsonExamples() {
    config := ServiceConfig{
        Name: "payment-service",
        Endpoints: []EndpointConfig{
            {Address: "10.0.0.1", Port: 8080, Weight: 1},
            {Address: "10.0.0.2", Port: 8080, Weight: 2},
        },
        LB:      "round-robin",
        Timeout: 5000,
        Retry:   &RetryConfig{MaxAttempts: 3, BackoffMs: 100},
        Labels:  map[string]string{"env": "prod", "team": "payments"},
    }

    // Marshal
    data, err := json.Marshal(config)
    if err != nil {
        panic(err)
    }
    fmt.Printf("JSON: %s\n", data)

    // Pretty print
    pretty, _ := json.MarshalIndent(config, "", "  ")
    fmt.Printf("Pretty:\n%s\n", pretty)

    // Unmarshal
    var decoded ServiceConfig
    if err := json.Unmarshal(data, &decoded); err != nil {
        panic(err)
    }
    fmt.Printf("Decoded: %+v\n", decoded)

    // Streaming encoder — for large responses
    var buf bytes.Buffer
    enc := json.NewEncoder(&buf)
    enc.SetEscapeHTML(false) // don't escape < > &
    enc.Encode(config)

    // Streaming decoder — for incoming request bodies
    dec := json.NewDecoder(&buf)
    var decoded2 ServiceConfig
    dec.Decode(&decoded2)

    // Unknown fields check
    dec2 := json.NewDecoder(bytes.NewReader([]byte(`{"name":"test","unknown":true}`)))
    dec2.DisallowUnknownFields()
    var cfg ServiceConfig
    if err := dec2.Decode(&cfg); err != nil {
        fmt.Println("Unknown field error:", err)
    }

    // Dynamic JSON with map
    var raw map[string]json.RawMessage
    json.Unmarshal(data, &raw)
    
    var name string
    json.Unmarshal(raw["name"], &name)
    fmt.Println("Name from raw:", name)
}

// Binary encoding — for data plane / packet processing
type PacketHeader struct {
    Version  uint8
    Type     uint8
    Length   uint16
    Sequence uint32
    Flags    uint32
}

const PacketHeaderSize = 12 // bytes

func (h *PacketHeader) Marshal() []byte {
    buf := make([]byte, PacketHeaderSize)
    buf[0] = h.Version
    buf[1] = h.Type
    binary.BigEndian.PutUint16(buf[2:], h.Length)
    binary.BigEndian.PutUint32(buf[4:], h.Sequence)
    binary.BigEndian.PutUint32(buf[8:], h.Flags)
    return buf
}

func (h *PacketHeader) Unmarshal(buf []byte) error {
    if len(buf) < PacketHeaderSize {
        return fmt.Errorf("buffer too small: %d < %d", len(buf), PacketHeaderSize)
    }
    h.Version  = buf[0]
    h.Type     = buf[1]
    h.Length   = binary.BigEndian.Uint16(buf[2:])
    h.Sequence = binary.BigEndian.Uint32(buf[4:])
    h.Flags    = binary.BigEndian.Uint32(buf[8:])
    return nil
}

// Using encoding/binary for structured reads
func readPacketFromConn(conn net.Conn) (*PacketHeader, []byte, error) {
    hdrBuf := make([]byte, PacketHeaderSize)
    
    // Read exact number of bytes
    if _, err := io.ReadFull(conn, hdrBuf); err != nil {
        return nil, nil, fmt.Errorf("read header: %w", err)
    }

    var hdr PacketHeader
    if err := hdr.Unmarshal(hdrBuf); err != nil {
        return nil, nil, err
    }

    if hdr.Length > 65535 {
        return nil, nil, fmt.Errorf("packet too large: %d", hdr.Length)
    }

    payload := make([]byte, hdr.Length)
    if _, err := io.ReadFull(conn, payload); err != nil {
        return nil, nil, fmt.Errorf("read payload: %w", err)
    }

    return &hdr, payload, nil
}

func main() {
    jsonExamples()

    hdr := &PacketHeader{
        Version:  1,
        Type:     2,
        Length:   100,
        Sequence: 42,
        Flags:    0,
    }
    
    data := hdr.Marshal()
    fmt.Printf("Marshaled: %v\n", data)

    var decoded PacketHeader
    decoded.Unmarshal(data)
    fmt.Printf("Decoded: %+v\n", decoded)
}
```

---

## 21. gRPC in Go

### 21.1 gRPC — Service Definition & Implementation

```protobuf
// proto/service.proto
syntax = "proto3";
package networking.v1;
option go_package = "github.com/myorg/myproject/gen/networking/v1";

message Endpoint {
  string address = 1;
  int32 port = 2;
  int32 weight = 3;
  map<string, string> labels = 4;
}

message RegisterRequest {
  string service_name = 1;
  Endpoint endpoint = 2;
}

message RegisterResponse {
  string id = 1;
  bool success = 2;
}

message DiscoverRequest {
  string service_name = 1;
  map<string, string> selector = 2;
}

message DiscoverResponse {
  repeated Endpoint endpoints = 1;
}

// Streaming health check
message HealthUpdate {
  string endpoint_id = 1;
  bool healthy = 2;
  int64 timestamp = 3;
}

service ServiceDiscovery {
  rpc Register(RegisterRequest) returns (RegisterResponse);
  rpc Discover(DiscoverRequest) returns (DiscoverResponse);
  
  // Server streaming — health updates
  rpc WatchHealth(DiscoverRequest) returns (stream HealthUpdate);
  
  // Client streaming — batch metrics
  rpc ReportMetrics(stream HealthUpdate) returns (RegisterResponse);
  
  // Bidirectional streaming
  rpc Sync(stream RegisterRequest) returns (stream RegisterResponse);
}
```

```go
// Server implementation
package grpcserver

import (
    "context"
    "fmt"
    "io"
    "net"
    "time"

    "google.golang.org/grpc"
    "google.golang.org/grpc/codes"
    "google.golang.org/grpc/credentials"
    "google.golang.org/grpc/keepalive"
    "google.golang.org/grpc/metadata"
    "google.golang.org/grpc/peer"
    "google.golang.org/grpc/reflection"
    "google.golang.org/grpc/status"
    
    pb "github.com/myorg/myproject/gen/networking/v1"
)

// Service implementation
type ServiceDiscoveryServer struct {
    pb.UnimplementedServiceDiscoveryServer
    
    registry map[string][]*pb.Endpoint
    mu       sync.RWMutex
    
    // Health watchers — for streaming
    watchers   map[string][]chan *pb.HealthUpdate
    watchersMu sync.Mutex
}

func NewServiceDiscoveryServer() *ServiceDiscoveryServer {
    return &ServiceDiscoveryServer{
        registry: make(map[string][]*pb.Endpoint),
        watchers: make(map[string][]chan *pb.HealthUpdate),
    }
}

// Unary RPC
func (s *ServiceDiscoveryServer) Register(
    ctx context.Context,
    req *RegisterRequest,
) (*RegisterResponse, error) {
    // Extract metadata (like HTTP headers)
    if md, ok := metadata.FromIncomingContext(ctx); ok {
        if auth := md.Get("authorization"); len(auth) > 0 {
            // validate token
            _ = auth[0]
        }
    }

    // Extract peer info
    if p, ok := peer.FromContext(ctx); ok {
        fmt.Printf("Request from: %s\n", p.Addr)
    }

    if req.ServiceName == "" {
        return nil, status.Error(codes.InvalidArgument, "service_name is required")
    }

    id := fmt.Sprintf("%s:%d", req.Endpoint.Address, req.Endpoint.Port)

    s.mu.Lock()
    s.registry[req.ServiceName] = append(s.registry[req.ServiceName], req.Endpoint)
    s.mu.Unlock()

    return &pb.RegisterResponse{Id: id, Success: true}, nil
}

func (s *ServiceDiscoveryServer) Discover(
    ctx context.Context,
    req *pb.DiscoverRequest,
) (*pb.DiscoverResponse, error) {
    s.mu.RLock()
    endpoints := s.registry[req.ServiceName]
    s.mu.RUnlock()

    if len(endpoints) == 0 {
        return nil, status.Errorf(codes.NotFound, "service %q not found", req.ServiceName)
    }

    return &pb.DiscoverResponse{Endpoints: endpoints}, nil
}

// Server streaming RPC
func (s *ServiceDiscoveryServer) WatchHealth(
    req *pb.DiscoverRequest,
    stream pb.ServiceDiscovery_WatchHealthServer,
) error {
    ch := make(chan *pb.HealthUpdate, 100)
    
    s.watchersMu.Lock()
    s.watchers[req.ServiceName] = append(s.watchers[req.ServiceName], ch)
    s.watchersMu.Unlock()

    defer func() {
        s.watchersMu.Lock()
        // Remove this watcher
        watchers := s.watchers[req.ServiceName]
        for i, w := range watchers {
            if w == ch {
                s.watchers[req.ServiceName] = append(watchers[:i], watchers[i+1:]...)
                break
            }
        }
        s.watchersMu.Unlock()
        close(ch)
    }()

    for {
        select {
        case update, ok := <-ch:
            if !ok {
                return nil
            }
            if err := stream.Send(update); err != nil {
                return status.Errorf(codes.Internal, "send failed: %v", err)
            }
        case <-stream.Context().Done():
            return stream.Context().Err()
        }
    }
}

// Client streaming RPC
func (s *ServiceDiscoveryServer) ReportMetrics(
    stream pb.ServiceDiscovery_ReportMetricsServer,
) error {
    count := 0
    for {
        update, err := stream.Recv()
        if err == io.EOF {
            // Client finished sending
            return stream.SendAndClose(&pb.RegisterResponse{
                Success: true,
                Id:      fmt.Sprintf("processed %d metrics", count),
            })
        }
        if err != nil {
            return status.Errorf(codes.Internal, "recv failed: %v", err)
        }
        count++
        _ = update
    }
}

// Start gRPC server
func RunGRPCServer(addr string) error {
    // Interceptors (like HTTP middleware)
    unaryInterceptors := grpc.ChainUnaryInterceptor(
        unaryLoggingInterceptor,
        unaryAuthInterceptor,
        unaryRecoveryInterceptor,
    )
    
    streamInterceptors := grpc.ChainStreamInterceptor(
        streamLoggingInterceptor,
    )

    server := grpc.NewServer(
        unaryInterceptors,
        streamInterceptors,
        grpc.KeepaliveParams(keepalive.ServerParameters{
            MaxConnectionIdle:     15 * time.Second,
            MaxConnectionAge:      30 * time.Minute,
            MaxConnectionAgeGrace: 5 * time.Second,
            Time:                  5 * time.Second,
            Timeout:               1 * time.Second,
        }),
        grpc.KeepaliveEnforcementPolicy(keepalive.EnforcementPolicy{
            MinTime:             5 * time.Second,
            PermitWithoutStream: true,
        }),
        grpc.MaxRecvMsgSize(4 * 1024 * 1024), // 4MB
        grpc.MaxSendMsgSize(4 * 1024 * 1024),
    )

    pb.RegisterServiceDiscoveryServer(server, NewServiceDiscoveryServer())
    reflection.Register(server) // enables grpcurl/grpc-cli introspection

    lis, err := net.Listen("tcp", addr)
    if err != nil {
        return err
    }

    fmt.Printf("gRPC server on %s\n", addr)
    return server.Serve(lis)
}

// Interceptors
func unaryLoggingInterceptor(
    ctx context.Context,
    req interface{},
    info *grpc.UnaryServerInfo,
    handler grpc.UnaryHandler,
) (interface{}, error) {
    start := time.Now()
    resp, err := handler(ctx, req)
    fmt.Printf("gRPC %s: %v in %v\n", info.FullMethod, status.Code(err), time.Since(start))
    return resp, err
}

func unaryAuthInterceptor(
    ctx context.Context,
    req interface{},
    info *grpc.UnaryServerInfo,
    handler grpc.UnaryHandler,
) (interface{}, error) {
    md, ok := metadata.FromIncomingContext(ctx)
    if !ok {
        return nil, status.Error(codes.Unauthenticated, "missing metadata")
    }
    tokens := md.Get("authorization")
    if len(tokens) == 0 || tokens[0] != "Bearer valid-token" {
        return nil, status.Error(codes.Unauthenticated, "invalid token")
    }
    return handler(ctx, req)
}

func unaryRecoveryInterceptor(
    ctx context.Context,
    req interface{},
    info *grpc.UnaryServerInfo,
    handler grpc.UnaryHandler,
) (resp interface{}, err error) {
    defer func() {
        if r := recover(); r != nil {
            err = status.Errorf(codes.Internal, "panic: %v", r)
        }
    }()
    return handler(ctx, req)
}

func streamLoggingInterceptor(
    srv interface{},
    ss grpc.ServerStream,
    info *grpc.StreamServerInfo,
    handler grpc.StreamHandler,
) error {
    start := time.Now()
    err := handler(srv, ss)
    fmt.Printf("gRPC stream %s: %v in %v\n", info.FullMethod, status.Code(err), time.Since(start))
    return err
}

// gRPC Client
func newGRPCClient(addr string) (pb.ServiceDiscoveryClient, error) {
    conn, err := grpc.Dial(addr,
        grpc.WithTransportCredentials(credentials.NewTLS(nil)), // or insecure.NewCredentials()
        grpc.WithKeepaliveParams(keepalive.ClientParameters{
            Time:                10 * time.Second,
            Timeout:             3 * time.Second,
            PermitWithoutStream: true,
        }),
        grpc.WithDefaultCallOptions(
            grpc.MaxCallRecvMsgSize(4*1024*1024),
            grpc.MaxCallSendMsgSize(4*1024*1024),
        ),
    )
    if err != nil {
        return nil, err
    }
    return pb.NewServiceDiscoveryClient(conn), nil
}

import "sync"
```

---

## 22. Timers, Tickers & Scheduling

### 22.1 time Package in Networking

```go
package main

import (
    "context"
    "fmt"
    "sync"
    "time"
)

func main() {
    // time.Timer — fire once after duration
    timer := time.NewTimer(100 * time.Millisecond)
    defer timer.Stop()

    select {
    case t := <-timer.C:
        fmt.Println("Timer fired at:", t)
    }

    // Reset timer — common pattern
    timer.Reset(50 * time.Millisecond)

    // time.After — convenience, but LEAKS if not drained
    // Use NewTimer + Stop for proper cleanup in production
    // Bad: select { case <-time.After(timeout): ... } in hot paths

    // time.Ticker — periodic execution
    ticker := time.NewTicker(100 * time.Millisecond)
    defer ticker.Stop()

    go func() {
        for t := range ticker.C {
            fmt.Println("Tick at:", t.Format("15:04:05.000"))
        }
    }()

    time.Sleep(350 * time.Millisecond)
}

// Health check scheduler — real-world pattern
type HealthChecker struct {
    endpoints []string
    interval  time.Duration
    timeout   time.Duration
    results   map[string]bool
    mu        sync.RWMutex
    done      chan struct{}
    wg        sync.WaitGroup
}

func NewHealthChecker(endpoints []string, interval time.Duration) *HealthChecker {
    return &HealthChecker{
        endpoints: endpoints,
        interval:  interval,
        timeout:   5 * time.Second,
        results:   make(map[string]bool),
        done:      make(chan struct{}),
    }
}

func (h *HealthChecker) Start() {
    for _, ep := range h.endpoints {
        h.wg.Add(1)
        go h.checkLoop(ep)
    }
}

func (h *HealthChecker) checkLoop(endpoint string) {
    defer h.wg.Done()

    // Stagger initial checks to avoid thundering herd
    jitter := time.Duration(len(endpoint)) * time.Millisecond
    
    timer := time.NewTimer(jitter)
    defer timer.Stop()

    // Wait for jitter before first check
    select {
    case <-timer.C:
    case <-h.done:
        return
    }

    ticker := time.NewTicker(h.interval)
    defer ticker.Stop()

    // Perform initial check
    h.check(endpoint)

    for {
        select {
        case <-ticker.C:
            h.check(endpoint)
        case <-h.done:
            return
        }
    }
}

func (h *HealthChecker) check(endpoint string) {
    ctx, cancel := context.WithTimeout(context.Background(), h.timeout)
    defer cancel()

    // Simulate health check
    healthy := true
    _ = ctx
    // conn, err := (&net.Dialer{}).DialContext(ctx, "tcp", endpoint)
    // if err != nil { healthy = false } else { conn.Close() }

    h.mu.Lock()
    h.results[endpoint] = healthy
    h.mu.Unlock()
}

func (h *HealthChecker) IsHealthy(endpoint string) bool {
    h.mu.RLock()
    defer h.mu.RUnlock()
    return h.results[endpoint]
}

func (h *HealthChecker) Stop() {
    close(h.done)
    h.wg.Wait()
}

// Exponential backoff with jitter — standard retry pattern
type Backoff struct {
    Initial  time.Duration
    Max      time.Duration
    Factor   float64
    Jitter   float64 // fraction of interval to jitter
    attempt  int
}

func (b *Backoff) Next() time.Duration {
    d := float64(b.Initial)
    for i := 0; i < b.attempt; i++ {
        d *= b.Factor
        if d > float64(b.Max) {
            d = float64(b.Max)
            break
        }
    }
    // Add jitter: random fraction of the base duration
    // jitter := d * b.Jitter * (rand.Float64()*2 - 1)
    // d += jitter
    b.attempt++
    return time.Duration(d)
}

func (b *Backoff) Reset() {
    b.attempt = 0
}

// Context-aware sleep
func sleepWithContext(ctx context.Context, d time.Duration) error {
    timer := time.NewTimer(d)
    defer timer.Stop()
    select {
    case <-timer.C:
        return nil
    case <-ctx.Done():
        return ctx.Err()
    }
}
```

---

## 23. File I/O & OS Interaction

### 23.1 OS Package for Network Config

```go
package main

import (
    "bufio"
    "fmt"
    "io"
    "os"
    "path/filepath"
    "strings"
)

func main() {
    // Reading network config files (e.g., /etc/hosts, /etc/resolv.conf)
    parseResolvConf("/etc/resolv.conf")
    parseHostsFile("/etc/hosts")

    // Environment variables — common in containers
    readNetworkConfig()

    // Writing IP tables rules to files
    writeIPTables("/tmp/iptables.rules")
}

func parseResolvConf(path string) {
    f, err := os.Open(path)
    if err != nil {
        fmt.Printf("Cannot open %s: %v\n", err)
        return
    }
    defer f.Close()

    var nameservers []string
    var search []string
    
    scanner := bufio.NewScanner(f)
    for scanner.Scan() {
        line := strings.TrimSpace(scanner.Text())
        if strings.HasPrefix(line, "#") || line == "" {
            continue
        }
        
        fields := strings.Fields(line)
        if len(fields) < 2 {
            continue
        }
        
        switch fields[0] {
        case "nameserver":
            nameservers = append(nameservers, fields[1])
        case "search", "domain":
            search = append(search, fields[1:]...)
        }
    }

    fmt.Printf("Nameservers: %v\n", nameservers)
    fmt.Printf("Search domains: %v\n", search)
}

func parseHostsFile(path string) {
    data, err := os.ReadFile(path)
    if err != nil {
        return
    }

    hosts := make(map[string][]string)
    
    for _, line := range strings.Split(string(data), "\n") {
        line = strings.TrimSpace(line)
        if strings.HasPrefix(line, "#") || line == "" {
            continue
        }
        
        fields := strings.Fields(line)
        if len(fields) < 2 {
            continue
        }
        
        ip := fields[0]
        for _, hostname := range fields[1:] {
            hosts[hostname] = append(hosts[hostname], ip)
        }
    }

    fmt.Printf("Hosts entries: %d\n", len(hosts))
}

func readNetworkConfig() {
    // Common env vars in containerized networking
    config := map[string]string{
        "POD_IP":           os.Getenv("POD_IP"),
        "NODE_IP":          os.Getenv("NODE_IP"),
        "POD_NAMESPACE":    os.Getenv("POD_NAMESPACE"),
        "SERVICE_CIDR":     os.Getenv("SERVICE_CIDR"),
        "CLUSTER_DNS":      os.Getenv("CLUSTER_DNS"),
    }
    
    for k, v := range config {
        if v != "" {
            fmt.Printf("%s=%s\n", k, v)
        }
    }
}

func writeIPTables(path string) error {
    rules := []string{
        "*filter",
        ":INPUT ACCEPT [0:0]",
        ":FORWARD ACCEPT [0:0]",
        ":OUTPUT ACCEPT [0:0]",
        "-A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT",
        "-A INPUT -p tcp --dport 8080 -j ACCEPT",
        "COMMIT",
    }

    // Write atomically — write to temp file then rename
    tmpPath := path + ".tmp"
    f, err := os.OpenFile(tmpPath, os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0644)
    if err != nil {
        return fmt.Errorf("create temp file: %w", err)
    }

    w := bufio.NewWriter(f)
    for _, rule := range rules {
        fmt.Fprintln(w, rule)
    }
    
    if err := w.Flush(); err != nil {
        f.Close()
        os.Remove(tmpPath)
        return fmt.Errorf("flush: %w", err)
    }
    
    if err := f.Sync(); err != nil { // fsync before rename
        f.Close()
        os.Remove(tmpPath)
        return fmt.Errorf("sync: %w", err)
    }
    
    f.Close()
    
    // Atomic rename
    return os.Rename(tmpPath, path)
}

// Watch for file changes — e.g., watching cert rotation
func watchFile(path string, onChange func()) error {
    var lastMod int64
    
    for {
        info, err := os.Stat(path)
        if err != nil {
            return err
        }
        
        modTime := info.ModTime().UnixNano()
        if lastMod != 0 && modTime != lastMod {
            onChange()
        }
        lastMod = modTime
    }
}

// Walking directories — for plugin discovery
func discoverCNIPlugins(dir string) []string {
    var plugins []string
    
    filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
        if err != nil {
            return nil // skip errors
        }
        if !info.IsDir() && info.Mode()&0111 != 0 {
            // Executable file
            plugins = append(plugins, path)
        }
        return nil
    })
    
    return plugins
}

// Pipes — for subprocess communication
func runIPCommand(args ...string) (string, error) {
    // Using os.Pipe for subprocess I/O
    r, w, err := os.Pipe()
    if err != nil {
        return "", err
    }
    defer r.Close()
    defer w.Close()
    
    // In real code you'd use os/exec package
    _ = args
    w.Close()
    
    data, err := io.ReadAll(r)
    return string(data), err
}
```

---

## 24. Reflection & the `unsafe` Package

### 24.1 Reflection — Dynamic Inspection

```go
package main

import (
    "fmt"
    "reflect"
    "unsafe"
)

type NetworkPolicy struct {
    Name      string
    Namespace string
    Port      int
    Protocol  string
    Enabled   bool
}

func inspectStruct(v interface{}) {
    t := reflect.TypeOf(v)
    val := reflect.ValueOf(v)

    // Dereference pointer
    if t.Kind() == reflect.Ptr {
        t = t.Elem()
        val = val.Elem()
    }

    fmt.Printf("Type: %s\n", t.Name())
    
    for i := 0; i < t.NumField(); i++ {
        field := t.Field(i)
        value := val.Field(i)
        
        tag := field.Tag.Get("json")
        fmt.Printf("  %s (%s) = %v [json:%s]\n",
            field.Name, field.Type, value.Interface(), tag)
    }
}

// Generic deep copy using reflection
func deepCopy(src interface{}) interface{} {
    t := reflect.TypeOf(src)
    val := reflect.ValueOf(src)
    
    if t.Kind() == reflect.Ptr {
        newVal := reflect.New(t.Elem())
        newVal.Elem().Set(val.Elem())
        return newVal.Interface()
    }
    
    newVal := reflect.New(t).Elem()
    newVal.Set(val)
    return newVal.Interface()
}

// unsafe — for high-performance networking code
func unsafeExamples() {
    // Convert []byte to string without allocation (DANGEROUS — string must not be modified)
    b := []byte("hello network")
    s := *(*string)(unsafe.Pointer(&b))
    fmt.Println(s) // "hello network"
    
    // Convert string to []byte without allocation (DANGEROUS — don't modify)
    str := "network packet"
    bs := *(*[]byte)(unsafe.Pointer(
        &struct {
            string
            cap int
        }{str, len(str)},
    ))
    fmt.Println(bs)
    
    // Struct layout — useful when working with kernel structures
    type TCPHeader struct {
        SrcPort  uint16
        DstPort  uint16
        SeqNum   uint32
        AckNum   uint32
        DataOff  uint8
        Flags    uint8
        WinSize  uint16
        Checksum uint16
        UrgPtr   uint16
    }
    
    hdr := TCPHeader{SrcPort: 1234, DstPort: 80}
    fmt.Printf("TCPHeader size: %d bytes\n", unsafe.Sizeof(hdr))
    fmt.Printf("SrcPort offset: %d\n", unsafe.Offsetof(hdr.SrcPort))
    fmt.Printf("DstPort offset: %d\n", unsafe.Offsetof(hdr.DstPort))
}

func main() {
    policy := &NetworkPolicy{
        Name:      "allow-http",
        Namespace: "default",
        Port:      8080,
        Protocol:  "TCP",
        Enabled:   true,
    }
    
    inspectStruct(policy)
    unsafeExamples()
}
```

---

## 25. Generics (Go 1.18+)

### 25.1 Generics for Networking Abstractions

```go
package main

import (
    "fmt"
    "sync"
)

// Generic ring buffer — useful for packet queues
type RingBuffer[T any] struct {
    buf    []T
    head   int
    tail   int
    count  int
    cap    int
    mu     sync.Mutex
}

func NewRingBuffer[T any](capacity int) *RingBuffer[T] {
    return &RingBuffer[T]{
        buf: make([]T, capacity),
        cap: capacity,
    }
}

func (r *RingBuffer[T]) Push(item T) bool {
    r.mu.Lock()
    defer r.mu.Unlock()
    if r.count == r.cap {
        return false // full
    }
    r.buf[r.tail] = item
    r.tail = (r.tail + 1) % r.cap
    r.count++
    return true
}

func (r *RingBuffer[T]) Pop() (T, bool) {
    r.mu.Lock()
    defer r.mu.Unlock()
    var zero T
    if r.count == 0 {
        return zero, false // empty
    }
    item := r.buf[r.head]
    r.head = (r.head + 1) % r.cap
    r.count--
    return item, true
}

func (r *RingBuffer[T]) Len() int {
    r.mu.Lock()
    defer r.mu.Unlock()
    return r.count
}

// Generic LRU cache — for connection caching, DNS caching
type LRUCache[K comparable, V any] struct {
    capacity int
    items    map[K]*lruItem[K, V]
    head     *lruItem[K, V] // most recently used
    tail     *lruItem[K, V] // least recently used
    mu       sync.Mutex
}

type lruItem[K comparable, V any] struct {
    key   K
    value V
    prev  *lruItem[K, V]
    next  *lruItem[K, V]
}

func NewLRUCache[K comparable, V any](capacity int) *LRUCache[K, V] {
    return &LRUCache[K, V]{
        capacity: capacity,
        items:    make(map[K]*lruItem[K, V]),
    }
}

func (c *LRUCache[K, V]) Get(key K) (V, bool) {
    c.mu.Lock()
    defer c.mu.Unlock()
    
    item, ok := c.items[key]
    if !ok {
        var zero V
        return zero, false
    }
    c.moveToFront(item)
    return item.value, true
}

func (c *LRUCache[K, V]) Set(key K, value V) {
    c.mu.Lock()
    defer c.mu.Unlock()
    
    if item, ok := c.items[key]; ok {
        item.value = value
        c.moveToFront(item)
        return
    }
    
    item := &lruItem[K, V]{key: key, value: value}
    c.items[key] = item
    c.addToFront(item)
    
    if len(c.items) > c.capacity {
        c.removeLast()
    }
}

func (c *LRUCache[K, V]) moveToFront(item *lruItem[K, V]) {
    if c.head == item {
        return
    }
    c.removeItem(item)
    c.addToFront(item)
}

func (c *LRUCache[K, V]) addToFront(item *lruItem[K, V]) {
    item.next = c.head
    item.prev = nil
    if c.head != nil {
        c.head.prev = item
    }
    c.head = item
    if c.tail == nil {
        c.tail = item
    }
}

func (c *LRUCache[K, V]) removeItem(item *lruItem[K, V]) {
    if item.prev != nil {
        item.prev.next = item.next
    } else {
        c.head = item.next
    }
    if item.next != nil {
        item.next.prev = item.prev
    } else {
        c.tail = item.prev
    }
}

func (c *LRUCache[K, V]) removeLast() {
    if c.tail == nil {
        return
    }
    delete(c.items, c.tail.key)
    c.removeItem(c.tail)
}

// Type constraints for networking
type Ordered interface {
    ~int | ~int8 | ~int16 | ~int32 | ~int64 |
    ~uint | ~uint8 | ~uint16 | ~uint32 | ~uint64 |
    ~float32 | ~float64 | ~string
}

func Min[T Ordered](a, b T) T {
    if a < b {
        return a
    }
    return b
}

func Max[T Ordered](a, b T) T {
    if a > b {
        return a
    }
    return b
}

// Generic result type — avoid error wrapping verbosity
type Result[T any] struct {
    value T
    err   error
}

func Ok[T any](v T) Result[T]       { return Result[T]{value: v} }
func Err[T any](e error) Result[T]  { return Result[T]{err: e} }

func (r Result[T]) Unwrap() (T, error) { return r.value, r.err }
func (r Result[T]) IsOk() bool          { return r.err == nil }

func main() {
    // Ring buffer
    rb := NewRingBuffer[[]byte](10)
    rb.Push([]byte("packet1"))
    rb.Push([]byte("packet2"))
    pkt, ok := rb.Pop()
    fmt.Printf("Got packet: %s, ok: %v\n", pkt, ok)

    // LRU cache
    cache := NewLRUCache[string, string](3)
    cache.Set("10.0.0.1", "backend-1")
    cache.Set("10.0.0.2", "backend-2")
    cache.Set("10.0.0.3", "backend-3")
    
    if ip, ok := cache.Get("10.0.0.1"); ok {
        fmt.Printf("Cached: %s\n", ip)
    }

    fmt.Println(Min(8080, 443))   // 443
    fmt.Println(Max("tcp", "udp")) // udp
}
```

---

## 26. Testing — Unit, Integration & Benchmarks

### 26.1 Comprehensive Testing for Network Code

```go
package networking_test

import (
    "bufio"
    "bytes"
    "context"
    "io"
    "net"
    "net/http"
    "net/http/httptest"
    "testing"
    "time"
)

// Unit test — basic
func TestParseEndpoint(t *testing.T) {
    tests := []struct {
        name    string
        input   string
        wantHost string
        wantPort int
        wantErr  bool
    }{
        {
            name:     "valid IPv4",
            input:    "10.0.0.1:8080",
            wantHost: "10.0.0.1",
            wantPort: 8080,
        },
        {
            name:     "valid IPv6",
            input:    "[::1]:8080",
            wantHost: "::1",
            wantPort: 8080,
        },
        {
            name:    "missing port",
            input:   "10.0.0.1",
            wantErr: true,
        },
        {
            name:    "empty string",
            input:   "",
            wantErr: true,
        },
    }

    for _, tc := range tests {
        t.Run(tc.name, func(t *testing.T) {
            host, port, err := parseEndpoint(tc.input)
            
            if tc.wantErr {
                if err == nil {
                    t.Errorf("expected error, got nil")
                }
                return
            }
            
            if err != nil {
                t.Fatalf("unexpected error: %v", err)
            }
            if host != tc.wantHost {
                t.Errorf("host: got %q, want %q", host, tc.wantHost)
            }
            if port != tc.wantPort {
                t.Errorf("port: got %d, want %d", port, tc.wantPort)
            }
        })
    }
}

func parseEndpoint(addr string) (string, int, error) {
    host, portStr, err := net.SplitHostPort(addr)
    if err != nil {
        return "", 0, err
    }
    port, err := net.LookupPort("tcp", portStr)
    if err != nil {
        return "", 0, err
    }
    return host, port, nil
}

// Testing with net.Pipe() — test without real network
func TestEchoServer(t *testing.T) {
    // net.Pipe creates a synchronous, in-memory connection pair
    server, client := net.Pipe()
    defer server.Close()
    defer client.Close()

    // Run echo server on server side
    go func() {
        io.Copy(server, server)
    }()

    // Test client side
    testData := []byte("hello, network!")
    
    _, err := client.Write(testData)
    if err != nil {
        t.Fatalf("Write failed: %v", err)
    }

    buf := make([]byte, len(testData))
    client.SetReadDeadline(time.Now().Add(time.Second))
    _, err = io.ReadFull(client, buf)
    if err != nil {
        t.Fatalf("Read failed: %v", err)
    }

    if !bytes.Equal(buf, testData) {
        t.Errorf("echo mismatch: got %q, want %q", buf, testData)
    }
}

// Testing TCP server with real listener
func TestTCPServer(t *testing.T) {
    // Listen on a random port
    listener, err := net.Listen("tcp", "127.0.0.1:0")
    if err != nil {
        t.Fatalf("Listen failed: %v", err)
    }
    defer listener.Close()

    addr := listener.Addr().String()
    t.Logf("Server on %s", addr)

    // Run server
    go func() {
        conn, err := listener.Accept()
        if err != nil {
            return
        }
        defer conn.Close()

        scanner := bufio.NewScanner(conn)
        for scanner.Scan() {
            conn.Write(append(scanner.Bytes(), '\n'))
        }
    }()

    // Connect client
    conn, err := net.DialTimeout("tcp", addr, time.Second)
    if err != nil {
        t.Fatalf("Dial failed: %v", err)
    }
    defer conn.Close()

    // Send data
    fmt.Fprintln(conn, "ping")

    // Read response
    conn.SetReadDeadline(time.Now().Add(time.Second))
    scanner := bufio.NewScanner(conn)
    if !scanner.Scan() {
        t.Fatal("Expected response")
    }
    if scanner.Text() != "ping" {
        t.Errorf("Got %q, want %q", scanner.Text(), "ping")
    }
}

// HTTP handler testing with httptest
func TestHealthEndpoint(t *testing.T) {
    handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        if r.Method != http.MethodGet {
            http.Error(w, "Method Not Allowed", http.StatusMethodNotAllowed)
            return
        }
        w.Header().Set("Content-Type", "application/json")
        w.WriteHeader(http.StatusOK)
        w.Write([]byte(`{"status":"healthy"}`))
    })

    // httptest.NewRecorder — no real HTTP connection
    req := httptest.NewRequest(http.MethodGet, "/healthz", nil)
    rec := httptest.NewRecorder()
    
    handler.ServeHTTP(rec, req)
    
    if rec.Code != http.StatusOK {
        t.Errorf("status: got %d, want %d", rec.Code, http.StatusOK)
    }
    
    contentType := rec.Header().Get("Content-Type")
    if contentType != "application/json" {
        t.Errorf("content-type: got %q, want application/json", contentType)
    }

    // httptest.NewServer — real HTTP server on random port
    server := httptest.NewServer(handler)
    defer server.Close()

    resp, err := http.Get(server.URL + "/healthz")
    if err != nil {
        t.Fatalf("GET failed: %v", err)
    }
    defer resp.Body.Close()
    
    if resp.StatusCode != http.StatusOK {
        t.Errorf("status: got %d, want %d", resp.StatusCode, http.StatusOK)
    }
    
    // TLS server
    tlsServer := httptest.NewTLSServer(handler)
    defer tlsServer.Close()
    
    client := tlsServer.Client() // client with test CA
    resp2, err := client.Get(tlsServer.URL + "/healthz")
    if err != nil {
        t.Fatalf("TLS GET failed: %v", err)
    }
    resp2.Body.Close()
}

// Context cancellation testing
func TestContextCancellation(t *testing.T) {
    ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
    defer cancel()

    ch := make(chan struct{})
    
    go func() {
        defer close(ch)
        select {
        case <-ctx.Done():
            // expected
        case <-time.After(time.Second):
            t.Error("Context not cancelled in time")
        }
    }()

    select {
    case <-ch:
        // goroutine exited cleanly
    case <-time.After(time.Second):
        t.Error("Goroutine leaked")
    }
}

// Benchmark tests
func BenchmarkParseEndpoint(b *testing.B) {
    addr := "192.168.1.100:8080"
    b.ReportAllocs()
    b.ResetTimer()
    
    for i := 0; i < b.N; i++ {
        _, _, _ = parseEndpoint(addr)
    }
}

func BenchmarkRingBufferPushPop(b *testing.B) {
    // rb := NewRingBuffer[[]byte](1000)
    pkt := make([]byte, 1500)
    
    b.ReportAllocs()
    b.RunParallel(func(pb *testing.PB) {
        _ = pkt
        for pb.Next() {
            // rb.Push(pkt)
            // rb.Pop()
        }
    })
}

// Table-driven parallel tests
func TestLoadBalancer(t *testing.T) {
    t.Parallel()
    
    tests := []struct{
        name     string
        backends []string
        requests int
        want     map[string]int // expected distribution
    }{
        {
            name:     "three backends round-robin",
            backends: []string{"a", "b", "c"},
            requests: 9,
            want:     map[string]int{"a": 3, "b": 3, "c": 3},
        },
    }
    
    for _, tc := range tests {
        tc := tc // capture range variable
        t.Run(tc.name, func(t *testing.T) {
            t.Parallel()
            
            counts := make(map[string]int)
            lb := &RoundRobinLB{}
            for _, b := range tc.backends {
                lb.AddBackend(b, 1)
            }
            
            for i := 0; i < tc.requests; i++ {
                backend, err := lb.SelectBackend(nil)
                if err != nil {
                    t.Fatalf("SelectBackend failed: %v", err)
                }
                counts[backend]++
            }
            
            for backend, wantCount := range tc.want {
                if counts[backend] != wantCount {
                    t.Errorf("backend %s: got %d requests, want %d",
                        backend, counts[backend], wantCount)
                }
            }
        })
    }
}

import "fmt"

type RoundRobinLB struct {
    backends []string
    counter  uint64
}

func (r *RoundRobinLB) SelectBackend(_ interface{}) (string, error) {
    if len(r.backends) == 0 {
        return "", fmt.Errorf("no backends")
    }
    idx := r.counter % uint64(len(r.backends))
    r.counter++
    return r.backends[idx], nil
}

func (r *RoundRobinLB) AddBackend(addr string, _ int) {
    r.backends = append(r.backends, addr)
}
```

---

## 27. Profiling & Performance Optimization

### 27.1 pprof & Benchmarking

```go
package main

import (
    "fmt"
    "net/http"
    _ "net/http/pprof" // registers /debug/pprof handlers
    "runtime"
    "runtime/debug"
    "time"
)

func init() {
    // Expose pprof endpoints — in production, use auth middleware
    go func() {
        http.ListenAndServe("localhost:6060", nil)
    }()
}

// Memory profiling
func profileMemory() {
    var stats runtime.MemStats
    runtime.ReadMemStats(&stats)
    
    fmt.Printf("Alloc: %d KB\n", stats.Alloc/1024)
    fmt.Printf("TotalAlloc: %d KB\n", stats.TotalAlloc/1024)
    fmt.Printf("HeapSys: %d KB\n", stats.HeapSys/1024)
    fmt.Printf("HeapInuse: %d KB\n", stats.HeapInuse/1024)
    fmt.Printf("NumGC: %d\n", stats.NumGC)
    fmt.Printf("GoroutineCount: %d\n", runtime.NumGoroutine())
}

// GC tuning for networking applications
func tuneGC() {
    // GOGC=200 means GC runs when heap doubles (default is 100)
    // Higher = less GC, more memory; Lower = more GC, less memory
    debug.SetGCPercent(200)
    
    // SetMemoryLimit — hard cap on memory (Go 1.19+)
    debug.SetMemoryLimit(512 * 1024 * 1024) // 512MB

    // Force GC
    runtime.GC()
}

// Object pooling — critical for high-throughput networking
import "sync"

var bufferPool = &sync.Pool{
    New: func() interface{} {
        buf := make([]byte, 32*1024)
        return &buf
    },
}

func processWithPool(data []byte) {
    // Get buffer from pool
    bufPtr := bufferPool.Get().(*[]byte)
    buf := *bufPtr
    defer bufferPool.Put(bufPtr) // return to pool
    
    // Use buf for processing...
    n := copy(buf, data)
    _ = buf[:n]
}

// CPU profiling
func profileCPU() {
    // Use via:
    // go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30
    // go tool pprof http://localhost:6060/debug/pprof/heap
    // go tool pprof http://localhost:6060/debug/pprof/goroutine
    
    // Or in tests:
    // go test -bench=. -cpuprofile=cpu.prof -memprofile=mem.prof
    // go tool pprof -http=:8080 cpu.prof
}

// GODEBUG for networking
func godebugHints() {
    // GODEBUG=netdns=go     — use Go's pure-Go DNS resolver
    // GODEBUG=netdns=cgo    — use cgo/system resolver
    // GODEBUG=tls13=0       — disable TLS 1.3
    // GODEBUG=gctrace=1     — print GC timing
    // GODEBUG=schedtrace=1000 — goroutine scheduler trace
    // GOMAXPROCS=4           — use 4 CPU cores
}

func main() {
    profileMemory()
    time.Sleep(time.Millisecond)
}
```

---

## 28. Memory Model & Garbage Collection

### 28.1 Go Memory Model — Happens-Before

```go
package main

import (
    "fmt"
    "sync"
    "sync/atomic"
)

// Go Memory Model: A write to a variable is guaranteed to be observed
// by a read ONLY if there's a "happens-before" relationship

// sync primitives establish happens-before:
// - Mutex.Unlock happens before subsequent Mutex.Lock
// - Channel send happens before channel receive completes
// - close(ch) happens before receive of zero value
// - sync.WaitGroup.Done happens before Wait returns
// - sync.Once.Do happens before any call returns

// DATA RACE — undefined behavior, always avoid
// var x int
// go func() { x = 1 }()  // write
// fmt.Println(x)           // concurrent read — DATA RACE

// CORRECT — using mutex
var (
    mu sync.Mutex
    x  int
)

func safeWrite() {
    mu.Lock()
    x = 1
    mu.Unlock()
}

func safeRead() int {
    mu.Lock()
    defer mu.Unlock()
    return x
}

// CORRECT — using atomic for simple values
var atomicX atomic.Int64

func atomicWrite() { atomicX.Store(1) }
func atomicRead() int64 { return atomicX.Load() }

// Escape analysis — understanding heap vs stack allocation
func stackAllocated() int {
    x := 42 // stays on stack
    return x
}

func heapAllocated() *int {
    x := 42
    return &x // escapes to heap — caller holds pointer
}

// minimize allocations in hot paths
func zeroAlloc(buf []byte, data []byte) []byte {
    // reuse provided buf instead of allocating
    buf = buf[:0]
    buf = append(buf, data...)
    return buf
}

func main() {
    safeWrite()
    fmt.Println(safeRead())

    atomicWrite()
    fmt.Println(atomicRead())
}
```

---

## 29. Build System, CGo & Syscalls

### 29.1 Build Tags, Cross-Compilation & Syscalls

```go
//go:build linux && amd64
// +build linux,amd64

// This file only compiles on Linux AMD64
// Used in networking for platform-specific syscalls

package networking

import (
    "fmt"
    "syscall"
    "unsafe"
    "golang.org/x/sys/unix"
)

// Raw sockets — for custom packet crafting/inspection
func createRawSocket() (int, error) {
    fd, err := syscall.Socket(
        syscall.AF_INET,     // IPv4
        syscall.SOCK_RAW,    // raw socket
        syscall.IPPROTO_TCP, // TCP protocol
    )
    if err != nil {
        return 0, fmt.Errorf("socket: %w", err)
    }
    return fd, nil
}

// Socket options — SO_REUSEPORT, TCP_NODELAY etc.
func setSocketOptions(fd int) error {
    // SO_REUSEPORT — multiple processes bind to same port
    if err := syscall.SetsockoptInt(fd, syscall.SOL_SOCKET, 
        syscall.SO_REUSEPORT, 1); err != nil {
        return fmt.Errorf("SO_REUSEPORT: %w", err)
    }
    
    // TCP_NODELAY — disable Nagle's algorithm (important for low-latency)
    if err := syscall.SetsockoptInt(fd, syscall.IPPROTO_TCP,
        syscall.TCP_NODELAY, 1); err != nil {
        return fmt.Errorf("TCP_NODELAY: %w", err)
    }
    
    // SO_KEEPALIVE
    if err := syscall.SetsockoptInt(fd, syscall.SOL_SOCKET,
        syscall.SO_KEEPALIVE, 1); err != nil {
        return fmt.Errorf("SO_KEEPALIVE: %w", err)
    }

    return nil
}

// eBPF socket attachment (Linux-specific)
func attachBPFFilter(fd int) error {
    // BPF filter to capture only TCP SYN packets
    filter := []syscall.SockFilter{
        {Code: 0x28, Jt: 0, Jf: 0, K: 0x0000000c}, // ldh [12]
        {Code: 0x15, Jt: 0, Jf: 4, K: 0x00000800}, // jeq #0x800
        {Code: 0x30, Jt: 0, Jf: 0, K: 0x00000017}, // ldb [23]
        {Code: 0x15, Jt: 0, Jf: 2, K: 0x00000006}, // jeq #6 (TCP)
        {Code: 0x30, Jt: 0, Jf: 0, K: 0x00000022}, // ldb [34]
        {Code: 0x45, Jt: 1, Jf: 0, K: 0x00000002}, // jset #2 (SYN)
        {Code: 0x6, Jt: 0, Jf: 0, K: 0x0000ffff},  // ret #65535
        {Code: 0x6, Jt: 0, Jf: 0, K: 0x00000000},  // ret #0
    }
    
    prog := &syscall.SockFprog{
        Len:    uint16(len(filter)),
        Filter: &filter[0],
    }
    
    _, _, errno := syscall.Syscall(
        syscall.SYS_SETSOCKOPT,
        uintptr(fd),
        uintptr(syscall.SOL_SOCKET),
        uintptr(syscall.SO_ATTACH_FILTER),
    )
    _ = prog
    if errno != 0 {
        return errno
    }
    return nil
}

// netlink — for Linux network configuration (used in CNI plugins)
func getRoutes() error {
    // github.com/vishvananda/netlink is the idiomatic library
    // But here's the raw syscall approach:
    fd, err := unix.Socket(unix.AF_NETLINK, unix.SOCK_RAW, unix.NETLINK_ROUTE)
    if err != nil {
        return fmt.Errorf("netlink socket: %w", err)
    }
    defer unix.Close(fd)
    
    // Bind to netlink
    sa := &unix.SockaddrNetlink{Family: unix.AF_NETLINK}
    if err := unix.Bind(fd, sa); err != nil {
        return fmt.Errorf("netlink bind: %w", err)
    }
    
    _ = unsafe.Pointer(nil) // suppress import
    fmt.Println("Netlink socket created")
    return nil
}
```

```bash
# Build tags for different platforms
# go build -tags integration ./...
# go build -tags !cgo ./...

# Makefile example for networking project
# build-linux:
#     CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
#     go build -a -installsuffix cgo \
#     -ldflags="-w -s -X main.version=${VERSION}" \
#     -o bin/agent-linux-amd64 ./cmd/agent

# Docker multi-stage build
# FROM golang:1.22 AS builder
# WORKDIR /app
# COPY go.* ./
# RUN go mod download
# COPY . .
# RUN CGO_ENABLED=0 go build -o agent ./cmd/agent
# 
# FROM gcr.io/distroless/static
# COPY --from=builder /app/agent /
# ENTRYPOINT ["/agent"]
```

---

## 30. Cloud-Native Patterns in Go

### 30.1 Production Patterns for Cloud-Native Networking

```go
package main

import (
    "context"
    "fmt"
    "net"
    "net/http"
    "os"
    "os/signal"
    "sync"
    "syscall"
    "time"
)

// =================== GRACEFUL SHUTDOWN ===================
type Application struct {
    httpServer *http.Server
    grpcServer interface{ GracefulStop() }
    listener   net.Listener
    wg         sync.WaitGroup
    cancel     context.CancelFunc
}

func (app *Application) Run() error {
    ctx, cancel := context.WithCancel(context.Background())
    app.cancel = cancel

    // Start servers
    go app.httpServer.ListenAndServe()

    // Wait for shutdown signal
    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM, syscall.SIGHUP)

    sig := <-sigCh
    fmt.Printf("Received signal: %s. Shutting down...\n", sig)

    // Cancel context — all goroutines watching ctx.Done() will exit
    cancel()

    // Graceful shutdown with timeout
    shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer shutdownCancel()

    // Stop accepting new connections
    app.httpServer.Shutdown(shutdownCtx)

    // Wait for in-flight requests to complete
    done := make(chan struct{})
    go func() {
        app.wg.Wait()
        close(done)
    }()

    select {
    case <-done:
        fmt.Println("Clean shutdown")
    case <-shutdownCtx.Done():
        fmt.Println("Forced shutdown — some requests may have been dropped")
    }

    _ = ctx
    return nil
}

// =================== CIRCUIT BREAKER ===================
type CircuitState int

const (
    CircuitClosed   CircuitState = iota // normal operation
    CircuitOpen                         // failing, reject requests
    CircuitHalfOpen                     // testing recovery
)

type CircuitBreaker struct {
    mu           sync.Mutex
    state        CircuitState
    failures     int
    successes    int
    lastFailure  time.Time
    
    maxFailures  int
    resetTimeout time.Duration
    halfOpenMax  int
}

func NewCircuitBreaker(maxFailures int, resetTimeout time.Duration) *CircuitBreaker {
    return &CircuitBreaker{
        state:        CircuitClosed,
        maxFailures:  maxFailures,
        resetTimeout: resetTimeout,
        halfOpenMax:  1,
    }
}

func (cb *CircuitBreaker) Execute(fn func() error) error {
    cb.mu.Lock()
    
    switch cb.state {
    case CircuitOpen:
        if time.Since(cb.lastFailure) > cb.resetTimeout {
            cb.state = CircuitHalfOpen
            cb.successes = 0
        } else {
            cb.mu.Unlock()
            return fmt.Errorf("circuit open: too many recent failures")
        }
    case CircuitHalfOpen:
        if cb.successes >= cb.halfOpenMax {
            cb.mu.Unlock()
            return fmt.Errorf("circuit half-open: waiting")
        }
    }
    
    cb.mu.Unlock()

    err := fn()

    cb.mu.Lock()
    defer cb.mu.Unlock()

    if err != nil {
        cb.failures++
        cb.lastFailure = time.Now()
        if cb.failures >= cb.maxFailures {
            cb.state = CircuitOpen
        }
        return err
    }

    // Success
    if cb.state == CircuitHalfOpen {
        cb.successes++
        if cb.successes >= cb.halfOpenMax {
            cb.state = CircuitClosed
            cb.failures = 0
        }
    }
    
    return nil
}

// =================== SERVICE DISCOVERY ===================
type ServiceRegistry struct {
    mu       sync.RWMutex
    services map[string][]ServiceInstance
    watchers map[string][]chan []ServiceInstance
}

type ServiceInstance struct {
    ID      string
    Address string
    Port    int
    Tags    map[string]string
    Healthy bool
}

func NewServiceRegistry() *ServiceRegistry {
    return &ServiceRegistry{
        services: make(map[string][]ServiceInstance),
        watchers: make(map[string][]chan []ServiceInstance),
    }
}

func (r *ServiceRegistry) Register(name string, instance ServiceInstance) {
    r.mu.Lock()
    defer r.mu.Unlock()
    
    r.services[name] = append(r.services[name], instance)
    r.notify(name)
}

func (r *ServiceRegistry) Watch(ctx context.Context, name string) <-chan []ServiceInstance {
    ch := make(chan []ServiceInstance, 10)
    
    r.mu.Lock()
    r.watchers[name] = append(r.watchers[name], ch)
    instances := r.services[name]
    r.mu.Unlock()
    
    // Send current state immediately
    if len(instances) > 0 {
        ch <- instances
    }
    
    // Cleanup on context cancellation
    go func() {
        <-ctx.Done()
        r.mu.Lock()
        watchers := r.watchers[name]
        for i, w := range watchers {
            if w == ch {
                r.watchers[name] = append(watchers[:i], watchers[i+1:]...)
                break
            }
        }
        r.mu.Unlock()
        close(ch)
    }()
    
    return ch
}

func (r *ServiceRegistry) notify(name string) {
    instances := r.services[name]
    for _, watcher := range r.watchers[name] {
        select {
        case watcher <- instances:
        default:
            // Watcher is slow — drop the update
        }
    }
}

// =================== RATE LIMITER ===================
type TokenBucket struct {
    mu       sync.Mutex
    tokens   float64
    maxTokens float64
    refillRate float64 // tokens per second
    lastRefill time.Time
}

func NewTokenBucket(rps float64, burst int) *TokenBucket {
    return &TokenBucket{
        tokens:     float64(burst),
        maxTokens:  float64(burst),
        refillRate: rps,
        lastRefill: time.Now(),
    }
}

func (tb *TokenBucket) Allow() bool {
    return tb.AllowN(1)
}

func (tb *TokenBucket) AllowN(n float64) bool {
    tb.mu.Lock()
    defer tb.mu.Unlock()
    
    now := time.Now()
    elapsed := now.Sub(tb.lastRefill).Seconds()
    tb.tokens = min(tb.maxTokens, tb.tokens+elapsed*tb.refillRate)
    tb.lastRefill = now
    
    if tb.tokens >= n {
        tb.tokens -= n
        return true
    }
    return false
}

func min(a, b float64) float64 {
    if a < b { return a }
    return b
}

// =================== OBSERVABILITY ===================
type Metrics struct {
    ConnectionsTotal   uint64
    ConnectionsActive  int64
    RequestsTotal      uint64
    RequestDuration    []time.Duration
    ErrorsTotal        uint64
    mu                 sync.Mutex
}

func (m *Metrics) RecordRequest(d time.Duration, err error) {
    m.RequestsTotal++
    m.mu.Lock()
    m.RequestDuration = append(m.RequestDuration, d)
    m.mu.Unlock()
    if err != nil {
        m.ErrorsTotal++
    }
}

func (m *Metrics) Percentile(p float64) time.Duration {
    m.mu.Lock()
    durations := make([]time.Duration, len(m.RequestDuration))
    copy(durations, m.RequestDuration)
    m.mu.Unlock()
    
    if len(durations) == 0 {
        return 0
    }
    
    // Sort and find percentile
    n := len(durations)
    idx := int(float64(n) * p / 100.0)
    if idx >= n { idx = n - 1 }
    return durations[idx]
}

func main() {
    fmt.Println("Cloud-native Go patterns ready for production")
    
    // Circuit breaker
    cb := NewCircuitBreaker(5, 30*time.Second)
    err := cb.Execute(func() error {
        // Call to backend service
        return nil
    })
    fmt.Println("Circuit breaker result:", err)

    // Token bucket rate limiter
    tb := NewTokenBucket(100, 10) // 100 RPS, burst of 10
    for i := 0; i < 5; i++ {
        fmt.Printf("Request %d allowed: %v\n", i, tb.Allow())
    }

    // Service registry
    registry := NewServiceRegistry()
    registry.Register("payment-service", ServiceInstance{
        ID:      "payment-1",
        Address: "10.0.0.1",
        Port:    8080,
        Healthy: true,
    })
    
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()
    
    ch := registry.Watch(ctx, "payment-service")
    instances := <-ch
    fmt.Printf("Found %d payment service instances\n", len(instances))
}
```

---

## Quick Reference: Must-Know Commands & Patterns

### Essential `go tool` Commands

```bash
# Race detector — ALWAYS run in CI
go test -race ./...

# CPU Profile
go test -bench=. -cpuprofile=cpu.prof ./pkg/...
go tool pprof -http=:8080 cpu.prof

# Memory Profile  
go test -bench=. -memprofile=mem.prof ./pkg/...
go tool pprof -http=:8080 mem.prof

# Trace (goroutine scheduling, GC, etc.)
go test -trace=trace.out ./pkg/...
go tool trace trace.out

# Find goroutine leaks
go test -run TestXxx -timeout 30s -v ./...

# Build with debugging
go build -gcflags="-N -l" ./...  # disable optimizations (for dlv/gdb)

# Check for escape analysis
go build -gcflags="-m=2" ./...

# Disassemble
go tool objdump -s "main.main" binary

# Check dependencies for vulnerabilities
govulncheck ./...

# Static analysis
staticcheck ./...
golangci-lint run --enable-all ./...
```

### Critical Networking Checklist

```
✅ Always defer conn.Close() immediately after acquiring connection
✅ Always set deadlines: conn.SetDeadline(time.Now().Add(timeout))
✅ Use context.WithTimeout for all dial/request operations
✅ Always check for context cancellation in server loops
✅ Use io.ReadFull for exact-byte reads over TCP
✅ Limit read sizes: io.LimitReader(r, maxBytes)
✅ Use bufio.Reader/Writer for small-chunk I/O over TCP
✅ Run tests with -race flag in CI
✅ Use sync.Pool for frequently allocated buffers
✅ Always close response bodies: defer resp.Body.Close()
✅ Use net.ListenConfig for socket option control
✅ Set TCP keep-alive on all long-lived connections
✅ Log remote address in connection handlers
✅ Use exponential backoff with jitter for retries
✅ Implement graceful shutdown with signal handling
✅ Expose /healthz, /readyz, and /metrics endpoints
✅ Use structured logging (zap/slog)
✅ Propagate context through ALL function calls
✅ Implement circuit breakers for upstream calls
✅ Never store context in struct fields
```

---

## Summary: Learning Path

```
Week 1-2: Fundamentals
├── Variables, types, control flow
├── Functions, closures, methods
├── Structs, interfaces, embedding
└── Error handling patterns

Week 3-4: Concurrency
├── Goroutines and the scheduler
├── Channels (buffered, unbuffered, directional)
├── select statement
└── sync package (Mutex, RWMutex, WaitGroup, Once, atomic)

Week 5-6: Standard Library Networking
├── net package (TCP, UDP, Unix sockets)
├── net/http (client, server, middleware)
├── crypto/tls (mTLS, certificate management)
└── context package (cancellation, deadlines)

Week 7-8: Advanced Topics
├── encoding (JSON, binary protocols)
├── gRPC and Protocol Buffers
├── Testing strategies (unit, integration, benchmarks)
└── Profiling with pprof

Week 9-10: Cloud-Native Patterns
├── Graceful shutdown
├── Circuit breakers and retries
├── Service discovery patterns
├── Syscalls and Linux networking APIs
└── Build system, CGo, eBPF integration
```

---

*This guide covers every mandatory concept for building production-grade cloud-native networking applications in Go. The topics build on each other — concurrency requires understanding goroutines + channels + sync; networking requires concurrency + context + error handling; cloud-native requires all of the above combined with production patterns.*