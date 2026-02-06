Yes! For Go, you can combine a file watcher with `go test` commands. Here are the main options:

**1. Using `entr` (simplest, cross-platform)**
```bash
ls **/*.go | entr -c go test -run TestP0001 -v
```

**2. Using `watchexec` (more features)**
```bash
watchexec -e go -c go test -run TestP0001 -v
```

**3. Using `gow` (Go-specific watcher)**
```bash
# Install: go install github.com/mitranim/gow@latest
gow test -run TestP0001 -v
```

**For your specific use case** (running a test with output):
```bash
# With entr
ls **/*.go | entr -c go test -v -run TestP0015

# With watchexec  
watchexec -e go -c 'go test -v -run TestP0015'

# With gow
gow test -v -run TestP0015
```

**Notes:**
- The `-run` flag in Go is like your Rust test filter - it takes a regex pattern
- Go shows output by default (no need for `--nocapture` equivalent)
- Add `-v` for verbose output to see all test output including `t.Log()` calls
- `entr` needs to be installed separately (`brew install entr` on macOS, or via your package manager)
- `watchexec` is the same tool that `cargo watch` uses under the hood

**My recommendation:** Try `gow` first if you want something Go-native and simple, or `watchexec` if you want more control and already use it with Rust.