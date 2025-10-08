# RustRover Ultimate Configuration & Cheat Sheet

## 1. Essential Keyboard Shortcuts to Memorize Today

### Navigation (The Big 5)
```
Ctrl+Shift+N    - Search files by name (fuzzy)
Ctrl+N          - Search for types/structs
Ctrl+Shift+A    - Find any action/command
Ctrl+E          - Recent files popup
Ctrl+B          - Go to definition (or Ctrl+Click)
```

### Editing Power Moves
```
Ctrl+Space      - Basic code completion
Ctrl+Shift+Space - Smart type-matching completion
Ctrl+/          - Toggle line comment
Ctrl+Shift+/    - Toggle block comment
Ctrl+D          - Duplicate line/selection
Ctrl+Y          - Delete line
Alt+Enter       - Show intention actions (quick fixes)
Ctrl+Alt+L      - Reformat code
```

### Refactoring Essentials
```
Shift+F6        - Rename (variable, function, module)
Ctrl+Alt+M      - Extract method
Ctrl+Alt+V      - Extract variable
Ctrl+Alt+C      - Extract constant
Ctrl+Alt+P      - Extract parameter
F2              - Next error/warning
Shift+F2        - Previous error/warning
```

### Code Generation
```
Alt+Insert      - Generate code (impl, tests, getters)
Ctrl+O          - Override methods
Ctrl+I          - Implement trait methods
Ctrl+Shift+T    - Create/navigate to test
```

### Debugging & Running
```
Shift+F10       - Run current configuration
Shift+F9        - Debug current configuration
Ctrl+F8         - Toggle breakpoint
F7              - Step into
F8              - Step over
Shift+F8        - Step out
F9              - Resume program
Ctrl+F2         - Stop
Alt+F9          - Run to cursor
```

### Multi-Cursor Magic
```
Alt+J           - Select next occurrence
Alt+Shift+J     - Unselect occurrence
Ctrl+Alt+Shift+J - Select all occurrences
Alt+Shift+Click - Add cursor at click position
Ctrl+Up/Down    - Move to prev/next method
```

### Window Management
```
Alt+1           - Project tool window
Alt+4           - Run tool window
Alt+5           - Debug tool window
Alt+9           - Git/Version Control
Ctrl+`          - Quick switch scheme (keymap, theme)
Ctrl+Shift+F12  - Maximize editor (hide all tool windows)
Shift+Escape    - Hide active tool window
```

---

## 2. RustRover Settings Configuration

**Note:** RustRover is a JetBrains IDE and uses its own configuration system (not VS Code's `settings.json`). Configuration is done through **File → Settings** (Ctrl+Alt+S).

### Key Settings to Configure

#### A. Code Completion Settings
Navigate to: **File → Settings → Editor → General → Code Completion**

```
✓ Show suggestions as you type
✓ Insert selected suggestion by pressing space, dot, or other context-dependent keys
✓ Show full method signatures
✓ Parameter info delay: 1000ms
Completion type: Smart type-matching
Sort suggestions by: Relevance
```

#### B. Rust-Specific Settings
Navigate to: **File → Settings → Languages & Frameworks → Rust**

```
✓ Use external linter: Clippy
✓ Run Clippy automatically
✓ Expand macros
✓ Show type hints
✓ Show parameter name hints
✓ Use Cargo check for code analysis
External linter additional arguments: -W clippy::all -W clippy::pedantic
```

#### C. Editor Inlay Hints
Navigate to: **File → Settings → Editor → Inlay Hints → Rust**

```
✓ Type hints
✓ Parameter hints
✓ Closure return type hints
✓ Chaining hints
✓ Binding mode hints
✓ Trait implementation hints
```

#### D. Auto-Import Settings
Navigate to: **File → Settings → Editor → General → Auto Import**

```
✓ Optimize imports on the fly
✓ Add unambiguous imports on the fly
Show import popup for: 1 variant
Insert imports for inner items: On the fly
```

#### E. Live Templates (Snippets)
Navigate to: **File → Settings → Editor → Live Templates → Rust**

Pre-configured templates include:
- `fn` → function template
- `test` → test function
- `mod` → module template
- `impl` → impl block
- `derive` → derive macro

**To create custom template:**
1. Settings → Editor → Live Templates
2. Click `+` → Live Template
3. Set abbreviation (e.g., `resmatch`)
4. Add template text:
```rust
match $EXPR$ {
    Ok($VAR$) => $END$,
    Err(e) => return Err(e.into()),
}
```
5. Define applicable context: Rust → Expression

---

## 3. Essential Extensions/Plugins for RustRover

RustRover is a dedicated Rust IDE with built-in Rust support. Additional plugins:

### Install Plugins via: File → Settings → Plugins

#### 1. **Toml** (Pre-installed)
For Cargo.toml editing.

**Settings:**
- Auto-completion enabled by default
- Syntax highlighting for dependencies

#### 2. **GitToolBox**
Enhanced Git integration.

**Settings (File → Settings → Other Settings → GitToolBox):**
```
✓ Show status inline
✓ Show commit dialog completion
✓ Auto-fetch every 15 minutes
Blame format: Author | Date | Message
```

#### 3. **Key Promoter X**
Learn shortcuts faster.

**Settings:**
```
Show notification after: 3 uses
✓ Buttons with shortcuts only
✓ Toolbar buttons
```

#### 4. **Rainbow Brackets**
Color-matched brackets for nested code.

**Settings:**
```
✓ Enable rainbow brackets
✓ Enable rainbow indent guides
Rainbow colors: Default scheme
```

#### 5. **.ignore**
For .gitignore, .dockerignore, etc.

**Settings:**
```
✓ Ignore file completion
✓ Templates support
```

#### 6. **Grep Console**
Colorize console output.

**Settings:**
```
✓ Enable colors
Error pattern: \berror\b|\bERROR\b
Warning pattern: \bwarning\b|\bWARN\b
```

---

## 4. Workflow #1: Fast Navigation

### Opening Files & Symbols

**Scenario:** Navigate a large Rust project quickly.

```bash
# 1. Open file by name (fuzzy search)
Ctrl+Shift+N
# Type: "main" → finds main.rs
# Type: "utl/par" → finds utils/parser.rs

# 2. Go to type/struct definition
Ctrl+N
# Type: "HashMap" → jump to HashMap definition

# 3. Go to symbol in current file
Ctrl+F12
# Shows structure view: all fns, structs, impls

# 4. Search everywhere (files + symbols + actions)
Double Shift (tap Shift twice)
# Type anything: files, classes, actions, settings

# 5. Recent files
Ctrl+E
# Shows recently opened files with preview

# 6. Recent locations (edits)
Ctrl+Shift+E
# Shows code snippets from recent editing locations
```

### Advanced Navigation

```bash
# Jump to trait implementation
Ctrl+Alt+B (on trait name)

# Show all usages of symbol
Alt+F7

# Find in files (grep)
Ctrl+Shift+F

# Navigate to next/prev method
Alt+Down / Alt+Up

# Go back/forward in navigation history
Ctrl+Alt+Left / Ctrl+Alt+Right

# Show file structure popup
Ctrl+F12 (stay focused in editor)

# Go to line number
Ctrl+G
```

**Example Workflow:**
```
1. Double Shift → Type "parse_config"
2. Ctrl+B on a function call → Jump to definition
3. Ctrl+Alt+Left → Go back
4. Alt+F7 → See all usages
5. Ctrl+E → Return to previous file
```

---

## 5. Workflow #2: Refactoring

### Rename Everything

```bash
# Rename variable/function/struct/module
Shift+F6
# - Updates all references
# - Updates module paths
# - Updates doc comments
# - Preview changes before applying
```

### Extract Refactorings

```bash
# 1. Extract Method
# Select code block → Ctrl+Alt+M
fn process_data(data: Vec<i32>) -> Result<i32, Error> {
    // Select these lines ↓
    let filtered: Vec<_> = data.iter()
        .filter(|&&x| x > 0)
        .copied()
        .collect();
    // After Ctrl+Alt+M:
    let filtered = filter_positive(data);
    // ...
}

# 2. Extract Variable
# Select expression → Ctrl+Alt+V
let result = data.iter().sum::<i32>() * 2 + offset;
// Select: data.iter().sum::<i32>()
// Ctrl+Alt+V → Name: "total"
let total = data.iter().sum::<i32>();
let result = total * 2 + offset;

# 3. Extract Constant
# Select literal → Ctrl+Alt+C
const MAX_RETRIES: u32 = 5;

# 4. Inline Variable/Function
# Cursor on variable → Ctrl+Alt+N
```

### Change Signature

```bash
# Refactor function parameters
Ctrl+F6 (on function name)
# - Reorder parameters
# - Add/remove parameters
# - Change parameter types
# - Updates all call sites
```

### Safe Delete

```bash
# Delete with usage search
Alt+Delete
# Searches project for usages before deleting
```

**Example Refactoring Session:**
```rust
// Before
fn calc(x: i32, y: i32) -> i32 {
    let z = x * 2 + y * 3;
    if z > 100 {
        return z - 50;
    }
    z
}

// 1. Extract "z - 50" → Ctrl+Alt+M → "apply_penalty"
// 2. Rename "calc" → Shift+F6 → "calculate_score"
// 3. Extract "100" → Ctrl+Alt+C → "THRESHOLD"
// 4. Change signature → Ctrl+F6 → Add "multiplier: i32"

// After
const THRESHOLD: i32 = 100;

fn calculate_score(x: i32, y: i32, multiplier: i32) -> i32 {
    let z = x * multiplier + y * 3;
    if z > THRESHOLD {
        return apply_penalty(z);
    }
    z
}

fn apply_penalty(z: i32) -> i32 {
    z - 50
}
```

---

## 6. Workflow #3: Debugging & Testing

### Running Tests

```bash
# Run single test (cursor in test fn)
Ctrl+Shift+F10

# Run all tests in file
Ctrl+Shift+F10 (cursor outside test fn)

# Run test with coverage
Alt+Shift+F10 → Select "Run with Coverage"

# Re-run last test
Shift+F10

# Debug last test
Shift+F9
```

### Debugging Workflow

```bash
# 1. Set breakpoint
Ctrl+F8 (on line number gutter)

# 2. Conditional breakpoint
Ctrl+Shift+F8
# Add condition: value > 100

# 3. Start debugging
Shift+F9

# 4. Step through code
F8 - Step over (next line)
F7 - Step into (enter function)
Shift+F8 - Step out (exit function)
Alt+F9 - Run to cursor

# 5. Evaluate expression
Alt+F8 (while debugging)
# Type any Rust expression to evaluate

# 6. Watch variables
# Right-click variable → Add to Watches

# 7. Resume program
F9

# 8. Stop debugging
Ctrl+F2
```

### Advanced Debugging

```bash
# Drop frame (go back in call stack)
Right-click on frame → Drop Frame

# Set value during debugging
F2 on variable in Variables pane

# Breakpoint actions
Ctrl+Shift+F8 on breakpoint
# - Log message without stopping
# - Disable until hit count
# - Chain to other breakpoints
```

### Test-Driven Development Workflow

```rust
// 1. Write test first
#[test]
fn test_parse_valid_input() {
    let result = parse_input("hello:42");
    assert_eq!(result.unwrap(), ("hello", 42));
}

// 2. Ctrl+Shift+T to create function
// Alt+Enter on red squiggle → "Create function parse_input"

// 3. Run test (Shift+F10) - it fails

// 4. Implement function
fn parse_input(s: &str) -> Result<(&str, i32), ParseError> {
    // Set breakpoint here with Ctrl+F8
    let parts: Vec<_> = s.split(':').collect();
    // ...
}

// 5. Debug test (Shift+F9)
// Step through with F8, evaluate expressions with Alt+F8

// 6. Fix until green
// Re-run with Shift+F10
```

**Debugging Checklist:**
```
✓ Breakpoint set? (Red dot in gutter)
✓ Running in Debug mode? (Shift+F9, not Shift+F10)
✓ Optimizations disabled? (Debug profile in Cargo.toml)
✓ DWARF symbols available? (debug = true in profile)
```

---

## 7. Quick Trigger: Suggestions & Inline Completions

### Manual Trigger Shortcuts

```bash
# Basic completion
Ctrl+Space
# Shows all available methods, fields, keywords

# Smart type-matching completion
Ctrl+Shift+Space
# Only shows items matching expected type
// Example:
fn process(value: String) {
    let x: usize = value.  ← Ctrl+Shift+Space
    // Only shows methods returning usize: len(), capacity(), etc.
}

# Postfix completion
Type expression, then dot + template
# Examples:
value.if     → if value { }
value.match  → match value { }
value.let    → let x = value;
value.return → return value;
vec![1,2,3].iter  → vec![1,2,3].iter()

# Show intention actions (AI-powered quick fixes)
Alt+Enter
# - Add missing imports
# - Implement trait
# - Convert to different syntax
# - Suggest optimizations

# Show parameter info
Ctrl+P (inside function call)
```

### AI Code Completion (if enabled)

RustRover supports AI Assistant features:

```bash
# Enable: File → Settings → Tools → AI Assistant

# Trigger full-line completion
# Type partial line, pause 300ms
let items: Vec<_> = data.iter().filter(|x|  ← AI suggests rest

# Accept suggestion
Tab (full line) or Ctrl+→ (word by word)

# Reject suggestion
Esc or keep typing

# AI chat for code generation
Ctrl+Shift+A → "AI Actions"
# Ask: "Generate a builder pattern for this struct"
```

---

## 8. Full IntelliSense Configuration for Rust

### Core Settings Path
**File → Settings → Editor → General → Code Completion**

### Essential Settings Checklist

```
[✓] Show suggestions as you type (auto-popup)
[✓] Insert suggestion by pressing Tab
[✓] Insert suggestion by pressing Space (for non-variable items)
[✓] Show full signatures in completion popup
[✓] Insert parentheses automatically for methods
[✓] Add unambiguous imports on the fly

Auto-popup delay: 0 ms
Parameter info delay: 1000 ms
Sort suggestions by: Relevance

Match case: First letter only
Show suggestions even if typing doesn't match case
```

### Language Server Configuration

RustRover uses its own Rust analysis engine + Cargo.

**File → Settings → Languages & Frameworks → Rust → Cargo**

```
[✓] Compile all project targets if possible
[✓] Fetch out-of-date dependencies automatically
[✓] Watch Cargo.toml
[✓] Use offline mode (for faster builds with cached deps)

Cargo command: check (faster than build)
External linter: Clippy
Additional arguments: -W clippy::pedantic
```

**File → Settings → Languages & Frameworks → Rust → Rustfmt**

```
[✓] Run rustfmt on Save
[✓] Use rustfmt instead of built-in formatter
Rustfmt path: (auto-detected from rustup)
```

### Keyboard Shortcuts for Suggestions

**File → Settings → Keymap → Search "completion"**

```
Basic completion: Ctrl+Space
Smart type completion: Ctrl+Shift+Space
Hippie completion: Alt+/
Cyclic expand word: Alt+/
Show intention actions: Alt+Enter
Parameter info: Ctrl+P
Quick documentation: Ctrl+Q
Next suggestion in list: Down or Ctrl+Down
Previous suggestion: Up or Ctrl+Up
Accept suggestion: Enter or Tab
Accept by character: Space, dot, semicolon (auto-configured)
```

### Live Template Shortcuts

**File → Settings → Editor → Live Templates → Rust**

Create custom templates:

```rust
// Abbreviation: "resmatch"
// Template text:
match $VAR$ {
    Ok(val) => $END$,
    Err(e) => return Err(e.into()),
}

// Abbreviation: "testcase"
#[test]
fn test_$NAME$() {
    $END$
}

// Abbreviation: "benchfn"
#[bench]
fn bench_$NAME$(b: &mut Bencher) {
    b.iter(|| {
        $END$
    });
}
```

**Usage:** Type abbreviation + Tab

---

## 9. Troubleshooting: When Suggestions Don't Appear

### Diagnostic Steps

```bash
# 1. Check if Rust toolchain is detected
File → Settings → Languages & Frameworks → Rust
# Verify "Toolchain location" points to ~/.cargo/bin

# 2. Check if project is indexed
# Bottom right corner: should say "Indexing: X% complete"
# Wait for indexing to finish

# 3. Invalidate caches
File → Invalidate Caches → Invalidate and Restart

# 4. Check Cargo build status
# Bottom status bar: "Cargo check: Running..."
# If stuck, run manually:
Ctrl+F9 (Build Project)

# 5. Verify dependencies are resolved
# Open Cargo.toml → See if dependencies are highlighted
# Run in terminal:
cargo fetch

# 6. Check for errors in Cargo output
Alt+4 (Run tool window) → Cargo tab
# Look for "error: ..." messages

# 7. Re-sync Cargo project
File → Reload Cargo Projects
# Or: Ctrl+Shift+A → "Reload Cargo Projects"

# 8. Check if file is excluded from project
# Right-click file → "Mark Directory as" should show "Unmark as..."

# 9. Verify Rust plugin is enabled
File → Settings → Plugins → Installed
# "Rust" should be checked

# 10. Check IDE logs
Help → Show Log in Files
# Look for Rust-related errors in idea.log
```

### Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| No completion for std types | Run `rustup component add rust-src` |
| Slow completion | Reduce `Cargo check` frequency in settings |
| Missing imports | Enable "Add unambiguous imports on the fly" |
| Stale suggestions | Ctrl+Shift+A → "Reload Cargo Projects" |
| No proc macro expansion | Install `rust-analyzer` component |
| Wrong suggestions | Check `Cargo.toml` edition (2021 recommended) |

---

## 10. Three Example Scenarios

### Scenario 1: Accepting Multi-Line AI Suggestion

```rust
// Context: Writing an HTTP handler
fn handle_request(req: Request) -> Response {
    // Start typing:
    let body = req.

    // ↓ AI suggests full completion (pause 300ms):
    let body = req.body()
        .map(|b| b.to_string())
        .unwrap_or_default();

    // Action:
    // Tab → Accept entire suggestion
    // Or Ctrl+→ → Accept word by word
    // Or Esc → Reject and continue typing

    // If suggestion is good but needs tweaking:
    // Tab to accept, then edit immediately
}
```

**Settings for better multi-line suggestions:**
```
File → Settings → Editor → General → Code Completion
[✓] Show full method signatures
[✓] Automatically show suggestions in 0ms

File → Settings → Tools → AI Assistant
[✓] Enable inline code completion
Suggestion delay: 300ms
Max suggestion length: 5 lines
```

### Scenario 2: Converting Suggestion to Reusable Snippet

```rust
// You've noticed AI often suggests this pattern:
let result = match value {
    Some(v) => v,
    None => return Err(Error::NotFound),
};

// Make it a Live Template:
// 1. Copy the pattern
// 2. File → Settings → Editor → Live Templates
// 3. Click + → Live Template
// 4. Abbreviation: "unwrapret"
// 5. Template text:
let $NAME$ = match $VAR$ {
    Some(v) => v,
    None => return Err($ERROR$),
};$END$

// 6. Variables:
//    - NAME: suggestVariableName()
//    - VAR: complete()
//    - ERROR: complete()
//    - END: cursor position after template

// 7. Define context: Rust → Expression

// Usage:
// Type: unwrapret<Tab>
// Fill in: VAR → value
// Fill in: ERROR → Error::NotFound
// Press Enter → cursor at $END$
```

**Power tip:** Convert any frequently used AI suggestion into a Live Template for instant reuse.

### Scenario 3: Disabling Noisy Suggestions

```rust
// Problem: Too many suggestions for common words
fn process_data(input: &str) {
    let data = inp  // ← 50 suggestions popup (annoying!)
}

// Solution 1: Increase auto-popup delay
File → Settings → Editor → General → Code Completion
Auto-popup delay: 500ms (instead of 0ms)

// Solution 2: Disable auto-popup, use manual trigger
[✗] Show suggestions as you type
// Now use Ctrl+Space when needed

// Solution 3: Filter suggestions by relevance
Sort suggestions by: Relevance (not Alphabetically)
[✓] Show suggestions even if typing doesn't match case

// Solution 4: Disable specific suggestion types
File → Settings → Editor → General → Code Completion
[✗] Suggest variable/parameter names in completion
[✗] Show matching words from file (if too noisy)

// Solution 5: Configure ML ranking
File → Settings → Tools → Machine Learning
[✓] Rank completion suggestions based on their relevance
Training data: Use my actions to improve suggestions

// For proc macros causing issues:
File → Settings → Languages & Frameworks → Rust → Expansion
[✗] Expand declarative macros (if causing lag)
```

**Optimal settings for focused coding:**
```
Auto-popup: 300ms delay
Smart completion: Ctrl+Shift+Space (manual only)
Postfix templates: Enabled (super useful)
ML-based ranking: Enabled
Parameter hints: Enabled for complex functions only
```

---

## 11. MCP Server Integration & Documentation

### Using External Documentation Servers

RustRover can integrate with documentation servers:

#### Quick Documentation Popup

```bash
# Show docs for symbol under cursor
Ctrl+Q
# Shows:
# - Function signature
# - Doc comments
# - Examples from doc tests
# - Links to external docs

# Open in tool window (persistent)
Ctrl+Q → Click "Open in Tool Window"
# Or: Ctrl+Shift+A → "Quick Documentation" → Tool Window
```

#### External Documentation

```bash
# Open docs.rs for crate
# Cursor on crate name in Cargo.toml → Shift+F1

# View local Cargo docs
# Terminal: cargo doc --open
# Or: Ctrl+Shift+A → "Cargo Doc"

# Custom MCP documentation server
# File → Settings → Tools → Web Browsers
# Add custom server:
Name: MCP Docs
URL: http://localhost:8080/docs/$MODULE$
# Use Shift+F1 to open
```

#### Cargo.toml Documentation Links

```toml
[package.metadata.docs.rs]
default-target = "x86_64-unknown-linux-gnu"
rustdoc-args = ["--cfg", "docsrs"]

# View with:
# Right-click dependency → "Go To" → "Documentation"
```

### MCP Server Workflow

```bash
# 1. Start MCP documentation server
# Terminal:
mcp-server start --port 8080

# 2. Configure RustRover external tool
# File → Settings → Tools → External Tools → Add
Name: Query MCP Docs
Program: curl
Arguments: -s http://localhost:8080/query?term=$SelectedText$
Working directory: $ProjectFileDir$
Output: Show console

# 3. Use:
# Select symbol → Ctrl+Shift+A → "Query MCP Docs"
# Or assign custom shortcut

# 4. For AI-assisted docs:
# Tools → AI Assistant → Chat
# Ask: "@mcp What does std::sync::Arc do?"
```

---

## 12. Creative Tips & Advanced Tricks

### 1. Macro Expansion Inspector

```bash
# View macro expansion inline
# Cursor on macro → Ctrl+Shift+A → "Show Rust Macro Expansion"
println!("Hello");  // ← Shows expanded code in tooltip

# Or use dedicated tool:
# Tools → Rust → Show Recursive Macro Expansion
```

### 2. Structural Search & Replace

```bash
# Advanced find/replace with AST patterns
# Edit → Find → Structural Search
# Example: Find all unwrap() calls
Template: $expr$.unwrap()
# Replace with: $expr$.expect("TODO: handle error")
```

### 3. Scratch Files for Experiments

```bash
# Create temporary Rust file
Ctrl+Shift+Alt+Insert → Rust
# Full IDE support without affecting project
# Perfect for testing snippets
```

### 4. Run Configurations from Comments

```rust
// CARGO: run --release --features "experimental"
// RUN_CONFIG: benchmark

fn main() {
    // IDE detects comments and creates run configs
}
```

### 5. Quick Definition Preview

```bash
# Peek at definition without leaving file
Ctrl+Shift+I (on symbol)
# Shows definition in popup
# Press again to open in split
```

### 6. Compare with Clipboard

```bash
# Compare selected code with clipboard
# Select code → Right-click → Compare with Clipboard
# Shows diff view
# Perfect for comparing AI suggestions
```

### 7. Postfix Completion Chains

```rust
// Type expressions backwards:
vec.iter.map.collect
// Tab after each dot completes to:
vec.iter().map(|x| ).collect()
```

### 8. Custom File Templates

```bash
# Create template for common files
# File → Settings → Editor → File and Code Templates
# Add "Rust Service" template:
#[derive(Debug)]
pub struct ${NAME}Service {
    // TODO
}

impl ${NAME}Service {
    pub fn new() -> Self {
        Self {}
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_${NAME|lowercase}() {
        // TODO
    }
}
```

### 9. HTTP Client for Testing APIs

```bash
# Create .http file in project
# Example: api-test.http

POST http://localhost:8080/api/users
Content-Type: application/json

{
  "name": "Alice"
}

###

GET http://localhost:8080/api/users/1

# Run with: Ctrl+Shift+F10
# Results show in HTTP Client tool window
```

### 10. Database Integration

```bash
# Connect to PostgreSQL/MySQL from IDE
# View → Tool Windows → Database
# Configure SQL dialect for sql! macros
# File → Settings → Languages & Frameworks → SQL Dialects
# Set project dialect to PostgreSQL
```

### 11. Git Integration Power Moves

```bash
# Annotate with Git Blame
# Right-click gutter → Annotate with Git Blame
# Shows author, date, commit for each line

# Compare with branch
# Right-click file → Git → Compare with Branch
# Select main → See diff

# Interactive Rebase
# Alt+9 (Git) → Log → Right-click commit
# → Interactively Rebase from Here

# Partial commits
# Ctrl+K (Commit) → Select specific chunks
# Commit only selected changes
```

### 12. Performance Profiling Integration

```bash
# Profile with Valgrind/Instruments
# Run → Edit Configurations → Add "Cargo Command"
# Command: build --profile profiling
# Before launch: Add "External Tool"
# Configure tool: valgrind --tool=callgrind
```

### 13. Dependency Graph Visualization

```bash
# View dependency tree
# Ctrl+Shift+A → "Show Cargo Dependency Graph"
# Visual graph of all dependencies
# Click nodes to view crate details
```

### 14. Regex Replace with Capture Groups

```bash
# Find: fn (\w+)\((.*?)\)
# Replace: pub fn $1($2) -> Result<(), Error>
# Converts private fns to public Result-returning
```

### 15. Custom Scopes for Focused Search

```bash
# Create custom scope
# Edit → Find → Find in Files
# Scope → Custom → Add
# Name: "Production Code"
# Pattern: file:src/*&&!file:*test*
# Exclude tests from search
```

---

## Quick Reference Card (Print This!)

```
NAVIGATION          | EDITING              | REFACTORING
--------------------|----------------------|------------------
Dbl Shift  - All    | Ctrl+Space  - Comp   | Shift+F6 - Rename
Ctrl+Shf+N - File   | Ctrl+/      - Cmnt   | Ctrl+Alt+M - Extr Method
Ctrl+N     - Type   | Alt+Enter   - Fix    | Ctrl+Alt+V - Extr Var
Ctrl+B     - Def    | Ctrl+D      - Dup    | Ctrl+Alt+P - Extr Param
Ctrl+E     - Recent | Ctrl+Alt+L  - Format | Ctrl+F6 - Change Sig
Alt+F7     - Usage  | Alt+Insert  - Gen    | Alt+Delete - Safe Del

DEBUG & TEST        | WINDOW MGMT          | POWER MOVES
--------------------|----------------------|------------------
Shift+F10  - Run    | Alt+1       - Proj   | Ctrl+Shf+A - Action
Shift+F9   - Debug  | Alt+4       - Run    | Ctrl+Q - Docs
Ctrl+F8    - Brkpt  | Alt+5       - Debug  | Alt+J - Multi-cursor
F8         - Over   | Alt+9       - Git    | Ctrl+Shf+I - Peek
F7         - Into   | Ctrl+`      - Scheme | Ctrl+Shf+F12 - MaxEdit
Alt+F8     - Eval   | Shf+Esc     - Hide   | Ctrl+Shf+T - Test
```

---

## Final Workflow Integration

### Morning Routine
```bash
1. Ctrl+E → Pick up where you left off
2. Alt+9 → Check git status
3. Shift+Shift → Find today's task (search TODOs)
4. Ctrl+Shift+F12 → Maximize editor
5. Ctrl+Space → Start coding with suggestions
```