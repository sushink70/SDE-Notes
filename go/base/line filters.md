# Line Filters in Go: A Comprehensive Guide

## What is a Line Filter?

A **line filter** is a program that:
1. Reads input line by line (typically from standard input - stdin)
2. Processes each line according to some logic
3. Writes output line by line (typically to standard output - stdout)

Think of it as a **pipeline stage** - data flows through it, gets transformed, and flows out. This is a fundamental Unix/Linux philosophy: small programs that do one thing well and can be chained together.

**Real-world analogy**: Imagine a factory assembly line where each station performs one specific task. A line filter is one such station for text processing.

---

## Core Concepts You Must Understand First

### 1. **Standard Streams**
Every program has three standard streams:
- **stdin** (standard input): Where input data comes from (file descriptor 0)
- **stdout** (standard output): Where normal output goes (file descriptor 1)  
- **stderr** (standard error): Where error messages go (file descriptor 2)

### 2. **Buffering**
**Buffer**: A temporary storage area in memory where data accumulates before being processed or written.

**Why buffering matters**: Reading/writing one byte at a time is slow (many system calls). Buffering reads/writes chunks of data, dramatically improving performance.

```
Without buffering: Read 1 byte → Process → Read 1 byte → Process...
With buffering:    Read 4096 bytes → Process all → Read next 4096 bytes...
```

### 3. **Delimiter**
**Delimiter**: A character that marks boundaries between data units.
- For line filters, the delimiter is typically `\n` (newline character)
- On Windows: `\r\n` (carriage return + line feed)
- On Unix/Linux: `\n`

---

## Architecture of a Line Filter

```
┌─────────────────────────────────────────────────────┐
│                   LINE FILTER                        │
│                                                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐     │
│  │          │    │          │    │          │     │
│  │  INPUT   │───▶│ PROCESS  │───▶│  OUTPUT  │     │
│  │ READER   │    │   LOGIC  │    │  WRITER  │     │
│  │          │    │          │    │          │     │
│  └──────────┘    └──────────┘    └──────────┘     │
│       ▲                                  │          │
│       │                                  ▼          │
│    stdin                              stdout        │
└─────────────────────────────────────────────────────┘
```

---

## Method 1: Scanner-Based Line Filter (Most Common)

### The Scanner Type

`bufio.Scanner` is Go's high-level, convenient way to read input line by line.

**Key characteristics**:
- Automatically handles buffering
- Splits input by delimiter (default: newline)
- Easy error handling
- Limited to ~64KB per line by default (configurable)

### Basic Template

```go
package main

import (
    "bufio"
    "fmt"
    "os"
)

func main() {
    // Create scanner reading from stdin
    scanner := bufio.NewScanner(os.Stdin)
    
    // scanner.Scan() returns true if there's a line to read
    // Returns false when EOF or error occurs
    for scanner.Scan() {
        line := scanner.Text()  // Get the current line (without \n)
        
        // Process the line
        processedLine := process(line)
        
        // Write to stdout
        fmt.Println(processedLine)
    }
    
    // Check for errors (important!)
    if err := scanner.Err(); err != nil {
        fmt.Fprintf(os.Stderr, "Error reading input: %v\n", err)
        os.Exit(1)
    }
}

func process(line string) string {
    // Your processing logic here
    return line
}
```

**Flow Diagram**:
```
Start
  │
  ▼
Create Scanner(os.Stdin)
  │
  ▼
scanner.Scan() ──No──▶ Check Error ──▶ Exit
  │ Yes                     │
  ▼                         │
Get line with scanner.Text() │
  │                         │
  ▼                         │
Process line                │
  │                         │
  ▼                         │
Output with fmt.Println()   │
  │                         │
  └─────────────────────────┘
```

### Example 1: Uppercase Filter

```go
package main

import (
    "bufio"
    "fmt"
    "os"
    "strings"
)

func main() {
    scanner := bufio.NewScanner(os.Stdin)
    
    for scanner.Scan() {
        line := scanner.Text()
        uppercased := strings.ToUpper(line)
        fmt.Println(uppercased)
    }
    
    if err := scanner.Err(); err != nil {
        fmt.Fprintf(os.Stderr, "Error: %v\n", err)
        os.Exit(1)
    }
}
```

**Usage**:
```bash
echo -e "hello\nworld" | go run uppercase.go
# Output:
# HELLO
# WORLD
```

---

## Method 2: Reader-Based Line Filter (More Control)

### The Reader Type

`bufio.Reader` provides more control than `Scanner`:
- Can read until any delimiter
- Can read fixed-size chunks
- Can peek at data without consuming it
- No line length limitations

### Basic Template

```go
package main

import (
    "bufio"
    "fmt"
    "io"
    "os"
)

func main() {
    reader := bufio.NewReader(os.Stdin)
    
    for {
        // ReadString reads until delimiter (inclusive)
        line, err := reader.ReadString('\n')
        
        // Handle EOF
        if err == io.EOF {
            // Process last line if it exists (no trailing newline)
            if len(line) > 0 {
                fmt.Print(process(line))
            }
            break
        }
        
        // Handle other errors
        if err != nil {
            fmt.Fprintf(os.Stderr, "Error: %v\n", err)
            os.Exit(1)
        }
        
        // Process and output
        fmt.Print(process(line))  // Note: Print, not Println (line has \n)
    }
}

func process(line string) string {
    return line
}
```

### Example 2: Number Lines

```go
package main

import (
    "bufio"
    "fmt"
    "io"
    "os"
)

func main() {
    reader := bufio.NewReader(os.Stdin)
    lineNumber := 1
    
    for {
        line, err := reader.ReadString('\n')
        
        if err == io.EOF {
            if len(line) > 0 {
                fmt.Printf("%d: %s", lineNumber, line)
            }
            break
        }
        
        if err != nil {
            fmt.Fprintf(os.Stderr, "Error: %v\n", err)
            os.Exit(1)
        }
        
        fmt.Printf("%d: %s", lineNumber, line)
        lineNumber++
    }
}
```

**Usage**:
```bash
cat file.txt | go run number_lines.go
# Output:
# 1: first line
# 2: second line
# 3: third line
```

---

## Method 3: Writer-Based Line Filter (Optimized Output)

### The Writer Type

`bufio.Writer` buffers output writes for better performance.

**Why use it?**: 
- Each `fmt.Println()` may trigger a system call
- `bufio.Writer` accumulates writes and flushes in chunks
- **Critical for high-throughput filters**

### Template with Buffered Writer

```go
package main

import (
    "bufio"
    "fmt"
    "os"
)

func main() {
    scanner := bufio.NewScanner(os.Stdin)
    writer := bufio.NewWriter(os.Stdout)
    
    // CRITICAL: Always flush before exit
    defer writer.Flush()
    
    for scanner.Scan() {
        line := scanner.Text()
        
        // Write to buffer (not directly to stdout)
        fmt.Fprintln(writer, process(line))
    }
    
    if err := scanner.Err(); err != nil {
        fmt.Fprintf(os.Stderr, "Error: %v\n", err)
        os.Exit(1)
    }
}

func process(line string) string {
    return line
}
```

**Performance Comparison**:
```
Without bufio.Writer: 1,000,000 lines → ~2.5 seconds
With bufio.Writer:    1,000,000 lines → ~0.8 seconds
```

---

## Advanced Patterns

### Pattern 1: Stateful Line Filter (Maintaining Context)

Sometimes you need to remember information across lines.

```go
package main

import (
    "bufio"
    "fmt"
    "os"
    "strings"
)

// Filter that removes consecutive duplicate lines
func main() {
    scanner := bufio.NewScanner(os.Stdin)
    writer := bufio.NewWriter(os.Stdout)
    defer writer.Flush()
    
    var previousLine string
    
    for scanner.Scan() {
        currentLine := scanner.Text()
        
        // Only print if different from previous line
        if currentLine != previousLine {
            fmt.Fprintln(writer, currentLine)
            previousLine = currentLine
        }
    }
    
    if err := scanner.Err(); err != nil {
        fmt.Fprintf(os.Stderr, "Error: %v\n", err)
        os.Exit(1)
    }
}
```

### Pattern 2: Multi-Pass Filter (Collecting All Lines First)

```go
package main

import (
    "bufio"
    "fmt"
    "os"
    "sort"
)

// Sort all input lines alphabetically
func main() {
    scanner := bufio.NewScanner(os.Stdin)
    var lines []string
    
    // First pass: collect all lines
    for scanner.Scan() {
        lines = append(lines, scanner.Text())
    }
    
    if err := scanner.Err(); err != nil {
        fmt.Fprintf(os.Stderr, "Error: %v\n", err)
        os.Exit(1)
    }
    
    // Process: sort
    sort.Strings(lines)
    
    // Second pass: output
    writer := bufio.NewWriter(os.Stdout)
    defer writer.Flush()
    
    for _, line := range lines {
        fmt.Fprintln(writer, line)
    }
}
```

**Trade-off**: Memory usage O(n) for n lines, but enables operations requiring full input.

### Pattern 3: Field-Based Processing (CSV/TSV Filters)

```go
package main

import (
    "bufio"
    "fmt"
    "os"
    "strings"
)

// Sum values in second column of TSV
func main() {
    scanner := bufio.NewScanner(os.Stdin)
    writer := bufio.NewWriter(os.Stdout)
    defer writer.Flush()
    
    total := 0
    
    for scanner.Scan() {
        line := scanner.Text()
        fields := strings.Split(line, "\t")
        
        if len(fields) < 2 {
            continue  // Skip malformed lines
        }
        
        var value int
        fmt.Sscanf(fields[1], "%d", &value)
        total += value
        
        fmt.Fprintln(writer, line)  // Pass through
    }
    
    if err := scanner.Err(); err != nil {
        fmt.Fprintf(os.Stderr, "Error: %v\n", err)
        os.Exit(1)
    }
    
    fmt.Fprintf(os.Stderr, "Total: %d\n", total)  // Summary to stderr
}
```

---

## Error Handling Strategies

### Strategy 1: Fail Fast (Strict)

```go
for scanner.Scan() {
    line := scanner.Text()
    
    result, err := riskyOperation(line)
    if err != nil {
        fmt.Fprintf(os.Stderr, "Error processing line: %v\n", err)
        os.Exit(1)  // Terminate immediately
    }
    
    fmt.Println(result)
}
```

### Strategy 2: Skip Bad Lines (Permissive)

```go
for scanner.Scan() {
    line := scanner.Text()
    
    result, err := riskyOperation(line)
    if err != nil {
        fmt.Fprintf(os.Stderr, "Warning: skipping line: %v\n", err)
        continue  // Skip this line, process next
    }
    
    fmt.Println(result)
}
```

### Strategy 3: Collect Errors (Report at End)

```go
var errors []error

for scanner.Scan() {
    line := scanner.Text()
    
    result, err := riskyOperation(line)
    if err != nil {
        errors = append(errors, err)
        continue
    }
    
    fmt.Println(result)
}

if len(errors) > 0 {
    fmt.Fprintf(os.Stderr, "Encountered %d errors:\n", len(errors))
    for _, err := range errors {
        fmt.Fprintf(os.Stderr, "  - %v\n", err)
    }
    os.Exit(1)
}
```

---

## Performance Optimization Techniques

### Technique 1: Custom Buffer Size

```go
scanner := bufio.NewScanner(os.Stdin)

// Default buffer: 64KB
// Increase for very long lines
const maxCapacity = 1024 * 1024  // 1MB
buf := make([]byte, maxCapacity)
scanner.Buffer(buf, maxCapacity)
```

### Technique 2: String Builder (Avoid String Concatenation)

```go
// BAD: Creates new string each iteration
result := ""
for scanner.Scan() {
    result += scanner.Text() + "\n"  // O(n²) complexity!
}

// GOOD: Use strings.Builder
var builder strings.Builder
for scanner.Scan() {
    builder.WriteString(scanner.Text())
    builder.WriteRune('\n')
}
result := builder.String()
```

### Technique 3: Avoid Unnecessary Allocations

```go
// BAD: Allocates new slice every line
for scanner.Scan() {
    fields := strings.Split(scanner.Text(), ",")  // New allocation
    process(fields)
}

// BETTER: Reuse buffer if possible
for scanner.Scan() {
    line := scanner.Text()
    // Process in place if you can
    processInPlace(line)
}
```

---

## Complete Real-World Example: grep Clone

```go
package main

import (
	"bufio"
	"flag"
	"fmt"
	"os"
	"regexp"
	"strings"
)

type Config struct {
	pattern     string
	caseInsens  bool
	invertMatch bool
	lineNumbers bool
	useRegex    bool
}

func main() {
	config := parseFlags()
	
	if err := grep(os.Stdin, os.Stdout, config); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}

func parseFlags() Config {
	var config Config
	
	flag.BoolVar(&config.caseInsens, "i", false, "Case insensitive")
	flag.BoolVar(&config.invertMatch, "v", false, "Invert match")
	flag.BoolVar(&config.lineNumbers, "n", false, "Show line numbers")
	flag.BoolVar(&config.useRegex, "E", false, "Use regex")
	flag.Parse()
	
	if flag.NArg() < 1 {
		fmt.Fprintln(os.Stderr, "Usage: grep [options] pattern")
		os.Exit(1)
	}
	
	config.pattern = flag.Arg(0)
	return config
}

func grep(input *os.File, output *os.File, config Config) error {
	scanner := bufio.NewScanner(input)
	writer := bufio.NewWriter(output)
	defer writer.Flush()
	
	// Prepare matcher
	matcher, err := createMatcher(config)
	if err != nil {
		return err
	}
	
	lineNum := 0
	
	for scanner.Scan() {
		lineNum++
		line := scanner.Text()
		
		matched := matcher(line)
		
		// Handle invert match
		if config.invertMatch {
			matched = !matched
		}
		
		if matched {
			if config.lineNumbers {
				fmt.Fprintf(writer, "%d:%s\n", lineNum, line)
			} else {
				fmt.Fprintln(writer, line)
			}
		}
	}
	
	return scanner.Err()
}

func createMatcher(config Config) (func(string) bool, error) {
	if config.useRegex {
		pattern := config.pattern
		if config.caseInsens {
			pattern = "(?i)" + pattern
		}
		
		re, err := regexp.Compile(pattern)
		if err != nil {
			return nil, fmt.Errorf("invalid regex: %w", err)
		}
		
		return re.MatchString, nil
	}
	
	// Simple substring matching
	return func(line string) bool {
		searchIn := line
		searchFor := config.pattern
		
		if config.caseInsens {
			searchIn = strings.ToLower(line)
			searchFor = strings.ToLower(config.pattern)
		}
		
		return strings.Contains(searchIn, searchFor)
	}, nil
}
```

**Usage**:
```bash
cat file.txt | go run grep.go -i -n "error"
# Shows lines containing "error" (case-insensitive) with line numbers
```

---

## Mental Models for Mastery

### Model 1: The Pipeline Mindset

```
Think: stdin → [your transform] → stdout

Your filter is ONE stage in a potentially long pipeline:
cat file | filter1 | filter2 | your_filter | filter3 > output
```

**Key insight**: Keep filters simple, composable, and single-purpose.

### Model 2: The Stream Processing Model

```
Data flows like water through a pipe:
- You can't go backwards (one-pass)
- Process as data arrives (don't wait for EOF)
- Minimize memory (don't buffer everything)
```

### Model 3: The Error Propagation Chain

```
Input Error → Processing Error → Output Error
     ↓              ↓                 ↓
   Handle        Handle            Handle
```

**Decision tree**:
1. Can I recover? → Skip/warn/default
2. Is it critical? → Fail fast
3. Is it expected? → Log and continue

---

## Common Pitfalls and Solutions

### Pitfall 1: Forgetting to Flush

```go
// BAD
writer := bufio.NewWriter(os.Stdout)
fmt.Fprintln(writer, "output")
// Program ends → buffer contents lost!

// GOOD
writer := bufio.NewWriter(os.Stdout)
defer writer.Flush()  // Ensures flush even on panic
fmt.Fprintln(writer, "output")
```

### Pitfall 2: Not Handling EOF Correctly with Reader

```go
// INCOMPLETE
for {
    line, err := reader.ReadString('\n')
    if err != nil {
        break  // Might lose last line if no trailing \n
    }
    process(line)
}

// COMPLETE
for {
    line, err := reader.ReadString('\n')
    
    if err == io.EOF {
        if len(line) > 0 {
            process(line)  // Handle last line
        }
        break
    }
    
    if err != nil {
        return err
    }
    
    process(line)
}
```

### Pitfall 3: Scanner Line Length Limits

```go
// Will fail on lines > 64KB
scanner := bufio.NewScanner(os.Stdin)

// Fixed
scanner := bufio.NewScanner(os.Stdin)
const maxCapacity = 10 * 1024 * 1024  // 10MB
buf := make([]byte, maxCapacity)
scanner.Buffer(buf, maxCapacity)
```

---

## Complexity Analysis

| Operation | Time | Space | Notes |
|-----------|------|-------|-------|
| Scanner.Scan() | O(n) per line | O(1) | Amortized, n = line length |
| Reader.ReadString() | O(n) per line | O(n) | Allocates new string |
| Writer.Flush() | O(m) | O(1) | m = buffer size |
| strings.Split() | O(n) | O(k) | k = number of fields |
| regexp.MatchString() | O(n·m) | O(1) | Worst case, n = text, m = pattern |

---

## Practice Exercises (Ordered by Difficulty)

1. **Basic**: Write a filter that counts lines
2. **Basic**: Write a filter that removes empty lines
3. **Intermediate**: Write a filter that extracts email addresses
4. **Intermediate**: Write a CSV field extractor (specific columns)
5. **Advanced**: Write a log analyzer (parse timestamps, count error levels)
6. **Advanced**: Write a JSON line filter (pretty-print each JSON object)
7. **Expert**: Write a streaming markdown-to-HTML converter

---

This guide equips you with the complete mental framework and technical toolkit for line filters in Go. The patterns you've learned here form the foundation of data processing pipelines—a critical skill for systems programming and distributed systems.

**Next step**: Implement one filter from scratch, measure its performance with large inputs, and optimize it using the techniques shown. This is deliberate practice in action.