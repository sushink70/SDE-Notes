# Ultimate VSCode + RustRover Development Setup

## 1. Essential Keyboard Shortcuts Cheatsheet

### VSCode - Core Navigation & Editing
```
NAVIGATION
Ctrl+P              Quick file open (fuzzy search)
Ctrl+Shift+P        Command palette
Ctrl+Shift+O        Go to symbol in file
Ctrl+T              Go to symbol in workspace
Ctrl+G              Go to line
Ctrl+Tab            Cycle through open files
Alt+Left/Right      Navigate back/forward
Ctrl+\              Split editor
Ctrl+1/2/3          Focus editor group

CODE EDITING
Ctrl+Space          Trigger IntelliSense manually
Ctrl+.              Quick fix / show code actions
F2                  Rename symbol
Ctrl+Shift+R        Refactor menu
Alt+Up/Down         Move line up/down
Ctrl+Shift+K        Delete line
Ctrl+D              Select next occurrence
Ctrl+Shift+L        Select all occurrences
Ctrl+/              Toggle line comment
Ctrl+Shift+A        Toggle block comment

INLINE SUGGESTIONS (Copilot/AI)
Tab                 Accept inline suggestion
Alt+]               Next inline suggestion
Alt+[               Previous inline suggestion
Ctrl+→              Accept next word of suggestion
Esc                 Dismiss suggestion

DEBUGGING
F5                  Start/continue debugging
F9                  Toggle breakpoint
F10                 Step over
F11                 Step into
Shift+F11           Step out
Ctrl+Shift+F5       Restart debugging

SEARCH & REPLACE
Ctrl+F              Find in file
Ctrl+H              Replace in file
Ctrl+Shift+F        Find in workspace
Ctrl+Shift+H        Replace in workspace
F3/Shift+F3         Find next/previous

TERMINAL
Ctrl+`              Toggle terminal
Ctrl+Shift+`        New terminal
```

### RustRover Shortcuts (IntelliJ-based)
```
NAVIGATION
Ctrl+N              Go to class/type
Ctrl+Shift+N        Go to file
Ctrl+Alt+Shift+N    Go to symbol
Ctrl+E              Recent files
Ctrl+Shift+E        Recent edited files
Ctrl+B              Go to declaration
Ctrl+Alt+B          Go to implementation
Ctrl+U              Go to super method

CODE EDITING
Ctrl+Space          Basic completion
Ctrl+Shift+Space    Smart type completion
Ctrl+Alt+L          Reformat code
Ctrl+Alt+O          Optimize imports
Ctrl+Shift+Enter    Complete statement
Ctrl+W              Extend selection
Shift+F6            Rename
Ctrl+Alt+M          Extract method
Ctrl+Alt+V          Extract variable

REFACTORING
Ctrl+Shift+Alt+T    Refactor this menu
Ctrl+Alt+N          Inline
Ctrl+F6             Change signature
```

---

## 2. Optimized settings.json

```json
{
  // ============================================================
  // EDITOR CORE SETTINGS
  // ============================================================
  "editor.fontSize": 14,
  "editor.lineHeight": 22,
  "editor.fontFamily": "'JetBrains Mono', 'Fira Code', 'Cascadia Code', Consolas, monospace",
  "editor.fontLigatures": true,
  "editor.tabSize": 4,
  "editor.insertSpaces": true,
  "editor.detectIndentation": true,
  "editor.wordWrap": "off",
  "editor.minimap.enabled": true,
  "editor.rulers": [80, 120],
  "editor.renderWhitespace": "boundary",
  "editor.bracketPairColorization.enabled": true,
  "editor.guides.bracketPairs": "active",
  "editor.stickyScroll.enabled": true,
  "editor.inlayHints.enabled": "on",
  
  // ============================================================
  // INTELLISENSE & SUGGESTIONS
  // ============================================================
  "editor.quickSuggestions": {
    "other": "on",
    "comments": "off",
    "strings": "on"
  },
  "editor.suggestOnTriggerCharacters": true,
  "editor.acceptSuggestionOnCommitCharacter": true,
  "editor.acceptSuggestionOnEnter": "on",
  "editor.suggestSelection": "first",
  "editor.snippetSuggestions": "top",
  "editor.suggest.preview": true,
  "editor.suggest.showWords": false,
  "editor.suggest.localityBonus": true,
  "editor.suggest.shareSuggestSelections": true,
  "editor.wordBasedSuggestions": "off",
  "editor.parameterHints.enabled": true,
  "editor.hover.enabled": true,
  "editor.hover.delay": 300,
  
  // ============================================================
  // INLINE SUGGESTIONS (Copilot/AI)
  // ============================================================
  "editor.inlineSuggest.enabled": true,
  "editor.inlineSuggest.showToolbar": "onHover",
  "github.copilot.enable": {
    "*": true,
    "plaintext": false,
    "markdown": true,
    "scminput": false
  },
  
  // ============================================================
  // AUTO-COMPLETION & IMPORTS
  // ============================================================
  "editor.formatOnSave": true,
  "editor.formatOnPaste": false,
  "editor.codeActionsOnSave": {
    "source.organizeImports": "explicit",
    "source.fixAll": "explicit"
  },
  
  // ============================================================
  // PYTHON SETTINGS
  // ============================================================
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.tabSize": 4,
    "editor.insertSpaces": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit",
      "source.fixAll": "explicit"
    }
  },
  "python.languageServer": "Pylance",
  "python.analysis.autoImportCompletions": true,
  "python.analysis.completeFunctionParens": true,
  "python.analysis.autoFormatStrings": true,
  "python.analysis.inlayHints.functionReturnTypes": true,
  "python.analysis.inlayHints.variableTypes": true,
  "python.analysis.inlayHints.parameterTypes": true,
  "python.analysis.typeCheckingMode": "basic",
  "python.analysis.diagnosticMode": "workspace",
  "python.analysis.autoSearchPaths": true,
  "python.analysis.extraPaths": [],
  "python.analysis.importFormat": "absolute",
  "python.analysis.indexing": true,
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.autoTestDiscoverOnSaveEnabled": true,
  
  // ============================================================
  // RUST SETTINGS
  // ============================================================
  "[rust]": {
    "editor.defaultFormatter": "rust-lang.rust-analyzer",
    "editor.formatOnSave": true,
    "editor.tabSize": 4,
    "editor.semanticHighlighting.enabled": true
  },
  "rust-analyzer.check.command": "clippy",
  "rust-analyzer.check.extraArgs": ["--all-targets"],
  "rust-analyzer.cargo.features": "all",
  "rust-analyzer.inlayHints.enable": true,
  "rust-analyzer.inlayHints.parameterHints.enable": true,
  "rust-analyzer.inlayHints.typeHints.enable": true,
  "rust-analyzer.inlayHints.chainingHints.enable": true,
  "rust-analyzer.completion.autoimport.enable": true,
  "rust-analyzer.completion.autoself.enable": true,
  "rust-analyzer.lens.enable": true,
  "rust-analyzer.lens.run.enable": true,
  "rust-analyzer.lens.debug.enable": true,
  "rust-analyzer.lens.implementations.enable": true,
  "rust-analyzer.hover.actions.enable": true,
  "rust-analyzer.hover.actions.references.enable": true,
  "rust-analyzer.assist.importGranularity": "module",
  
  // ============================================================
  // GO SETTINGS
  // ============================================================
  "[go]": {
    "editor.defaultFormatter": "golang.go",
    "editor.formatOnSave": true,
    "editor.tabSize": 4,
    "editor.insertSpaces": false,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit"
    }
  },
  "go.useLanguageServer": true,
  "go.languageServerFlags": ["-rpc.trace"],
  "go.lintTool": "golangci-lint",
  "go.lintOnSave": "workspace",
  "go.formatTool": "goimports",
  "go.autocompleteUnimportedPackages": true,
  "go.gotoSymbol.includeImports": true,
  "go.inlayHints.assignVariableTypes": true,
  "go.inlayHints.compositeLiteralFieldTypes": true,
  "go.inlayHints.constantValues": true,
  "go.inlayHints.functionTypeParameters": true,
  "go.inlayHints.parameterNames": true,
  "go.inlayHints.rangeVariableTypes": true,
  "gopls": {
    "ui.completion.usePlaceholders": true,
    "ui.semanticTokens": true,
    "ui.codelenses": {
      "generate": true,
      "test": true
    }
  },
  
  // ============================================================
  // TYPESCRIPT/JAVASCRIPT SETTINGS
  // ============================================================
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true,
    "editor.tabSize": 2,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit",
      "source.fixAll.eslint": "explicit"
    }
  },
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.formatOnSave": true,
    "editor.tabSize": 2
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.tabSize": 2
  },
  "[javascriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.tabSize": 2
  },
  "typescript.updateImportsOnFileMove.enabled": "always",
  "typescript.suggest.autoImports": true,
  "typescript.suggest.completeFunctionCalls": true,
  "typescript.suggest.includeAutomaticOptionalChainCompletions": true,
  "typescript.inlayHints.parameterNames.enabled": "all",
  "typescript.inlayHints.functionLikeReturnTypes.enabled": true,
  "typescript.inlayHints.variableTypes.enabled": true,
  "typescript.inlayHints.propertyDeclarationTypes.enabled": true,
  "typescript.inlayHints.enumMemberValues.enabled": true,
  "javascript.suggest.autoImports": true,
  "javascript.updateImportsOnFileMove.enabled": "always",
  "javascript.inlayHints.parameterNames.enabled": "all",
  
  // ============================================================
  // FILES & WORKSPACE
  // ============================================================
  "files.autoSave": "onFocusChange",
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true,
  "files.exclude": {
    "**/.git": true,
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/.mypy_cache": true,
    "**/target": true,
    "**/node_modules": true,
    "**/.DS_Store": true
  },
  "search.exclude": {
    "**/node_modules": true,
    "**/target": true,
    "**/.venv": true,
    "**/venv": true
  },
  
  // ============================================================
  // TERMINAL
  // ============================================================
  "terminal.integrated.fontSize": 13,
  "terminal.integrated.fontFamily": "'JetBrains Mono', monospace",
  "terminal.integrated.cursorBlinking": true,
  "terminal.integrated.cursorStyle": "line",
  "terminal.integrated.scrollback": 10000,
  
  // ============================================================
  // GIT
  // ============================================================
  "git.enableSmartCommit": true,
  "git.confirmSync": false,
  "git.autofetch": true,
  "git.openRepositoryInParentFolders": "always",
  "diffEditor.ignoreTrimWhitespace": false,
  
  // ============================================================
  // WORKBENCH
  // ============================================================
  "workbench.colorTheme": "One Dark Pro",
  "workbench.iconTheme": "material-icon-theme",
  "workbench.editor.highlightModifiedTabs": true,
  "workbench.editor.enablePreview": false,
  "workbench.startupEditor": "none",
  "breadcrumbs.enabled": true,
  
  // ============================================================
  // PERFORMANCE
  // ============================================================
  "extensions.ignoreRecommendations": false,
  "telemetry.telemetryLevel": "off",
  "update.mode": "start"
}
```

---

## 3. Essential Extensions with Configuration

### Python Extensions

**1. Python (ms-python.python)**
```json
{
  "python.defaultInterpreterPath": "/usr/bin/python3",
  "python.terminal.activateEnvironment": true,
  "python.terminal.executeInFileDir": true
}
```

**2. Pylance (ms-python.vscode-pylance)**
```json
{
  "python.analysis.typeCheckingMode": "basic",
  "python.analysis.diagnosticSeverityOverrides": {
    "reportUnusedVariable": "warning",
    "reportGeneralTypeIssues": "warning"
  }
}
```

**3. Ruff (charliermarsh.ruff)**
```json
{
  "ruff.enable": true,
  "ruff.organizeImports": true,
  "ruff.fixAll": true,
  "ruff.lint.args": ["--select=E,F,I,N,W"]
}
```

**4. Python Test Explorer (littlefoxteam.vscode-python-test-adapter)**
- Auto-discovers pytest tests
- Visual test runner in sidebar

**5. autoDocstring (njpwerner.autodocstring)**
```json
{
  "autoDocstring.docstringFormat": "google",
  "autoDocstring.startOnNewLine": false,
  "autoDocstring.generateDocstringOnEnter": true
}
```

### Rust Extensions

**1. rust-analyzer (rust-lang.rust-analyzer)**
```json
{
  "rust-analyzer.procMacro.enable": true,
  "rust-analyzer.cargo.loadOutDirsFromCheck": true,
  "rust-analyzer.rustfmt.extraArgs": ["+nightly"],
  "rust-analyzer.diagnostics.disabled": []
}
```

**2. crates (serayuzgur.crates)**
```json
{
  "crates.listPreReleases": false,
  "crates.useLocalIndex": true
}
```

**3. Even Better TOML (tamasfe.even-better-toml)**
- Syntax highlighting and validation for Cargo.toml

**4. CodeLLDB (vadimcn.vscode-lldb)**
```json
{
  "lldb.displayFormat": "auto",
  "lldb.showDisassembly": "auto",
  "lldb.dereferencePointers": true
}
```

### Go Extensions

**1. Go (golang.go)**
```json
{
  "go.toolsManagement.autoUpdate": true,
  "go.testFlags": ["-v", "-race"],
  "go.coverOnSave": false,
  "go.coverageDecorator": {
    "type": "gutter"
  }
}
```

**2. Go Test Explorer (premparihar.gotestexplorer)**
- Visual test runner

### TypeScript/JavaScript Extensions

**1. ESLint (dbaeumer.vscode-eslint)**
```json
{
  "eslint.validate": [
    "javascript",
    "javascriptreact",
    "typescript",
    "typescriptreact"
  ],
  "eslint.format.enable": true,
  "eslint.codeActionsOnSave.mode": "all"
}
```

**2. Prettier (esbenp.prettier-vscode)**
```json
{
  "prettier.singleQuote": true,
  "prettier.trailingComma": "es5",
  "prettier.printWidth": 100,
  "prettier.semi": true
}
```

**3. Path Intellisense (christian-kohler.path-intellisense)**
```json
{
  "typescript.preferences.importModuleSpecifier": "relative",
  "javascript.preferences.importModuleSpecifier": "relative"
}
```

### Universal Extensions

**1. GitLens (eamodio.gitlens)**
```json
{
  "gitlens.currentLine.enabled": true,
  "gitlens.codeLens.enabled": true,
  "gitlens.hovers.currentLine.over": "line"
}
```

**2. Error Lens (usernamehw.errorlens)**
```json
{
  "errorLens.enabled": true,
  "errorLens.fontSize": "0.9em",
  "errorLens.delay": 500
}
```

**3. Todo Tree (gruntfuggly.todo-tree)**
```json
{
  "todo-tree.general.tags": ["TODO", "FIXME", "HACK", "NOTE", "BUG"],
  "todo-tree.highlights.useColourScheme": true
}
```

**4. Bookmarks (alefragnani.bookmarks)**
- Quick navigation to marked lines

**5. Remote - SSH (ms-vscode-remote.remote-ssh)**
- Develop on remote servers

---

## 4. Three Essential Workflows

### Workflow 1: Fast Navigation

**Scenario: Finding and jumping to code**

```bash
# 1. FUZZY FILE SEARCH
Ctrl+P → Type partial filename → Enter
Example: "usr_mod" finds "user_module.py"

# 2. SYMBOL IN FILE
Ctrl+Shift+O → Type function/class name
Example: "@get_user" jumps to get_user function

# 3. WORKSPACE SYMBOL SEARCH
Ctrl+T → Type symbol across all files
Example: "#UserModel" finds class in any file

# 4. GO TO DEFINITION
Ctrl+Click on symbol OR F12
Example: Click on function call → jumps to definition

# 5. PEEK DEFINITION (inline view)
Alt+F12 → Shows definition in popup

# 6. GO TO IMPLEMENTATION
Ctrl+F12 → Jump to implementation (not interface)

# 7. FIND ALL REFERENCES
Shift+F12 → Shows all usages of symbol

# 8. BREADCRUMB NAVIGATION
Ctrl+Shift+. → Navigate file structure from top bar

# 9. RECENT FILES
Ctrl+Tab → Cycle through recent files
Ctrl+R → Open recent workspace/folder

# 10. MULTI-FILE SEARCH
Ctrl+Shift+F → Search text across workspace
Add "*.py" in files to include pattern
```

**Pro Tips:**
- Use `Ctrl+P` then type `:line_number` to jump to specific line
- Use `Ctrl+P` then type `@symbol` for file symbols
- Use `Ctrl+P` then type `#symbol` for workspace symbols
- Enable "Breadcrumbs" for quick file structure navigation

### Workflow 2: Refactoring

**Scenario: Cleaning and restructuring code**

```bash
# 1. RENAME SYMBOL (ALL REFERENCES)
F2 → Type new name → Enter
Works across all files in workspace

# 2. EXTRACT FUNCTION/METHOD
Select code → Ctrl+Shift+R → "Extract to function"
Or: Right-click → Refactor → Extract function

# 3. EXTRACT VARIABLE
Select expression → Ctrl+Shift+R → "Extract to variable"

# 4. ORGANIZE IMPORTS
Shift+Alt+O
Or auto on save with codeActionsOnSave setting

# 5. QUICK FIX / CODE ACTIONS
Ctrl+. → Shows available fixes and refactorings
Example: Add missing import, implement interface, etc.

# 6. FORMAT DOCUMENT
Shift+Alt+F → Formats entire file

# 7. FORMAT SELECTION
Select code → Shift+Alt+F

# 8. MULTI-CURSOR REFACTORING
Ctrl+D → Select next occurrence
Ctrl+Shift+L → Select all occurrences
Type to edit all at once

# 9. CHANGE ALL OCCURRENCES
Ctrl+F2 → Select all instances of symbol
Type to change all

# 10. MOVE FILE AND UPDATE IMPORTS
F1 → "Move File to..." → Automatically updates imports
```

**Python-Specific Refactoring:**
```python
# Extract method example:
# Before:
def process_data(data):
    # Select these 3 lines
    cleaned = [x.strip() for x in data]
    filtered = [x for x in cleaned if x]
    return sorted(filtered)

# After extract (Ctrl+Shift+R):
def process_data(data):
    return clean_and_sort(data)

def clean_and_sort(data):
    cleaned = [x.strip() for x in data]
    filtered = [x for x in cleaned if x]
    return sorted(filtered)
```

**Rust-Specific Refactoring:**
```rust
// Fill match arms: Ctrl+. on incomplete match
match value {
    Some(x) => {},
    // Cursor here, Ctrl+. → "Fill match arms"
}

// Convert if-let to match: Ctrl+.
if let Some(x) = value {
    // code
}
// → Convert to match statement
```

### Workflow 3: Debugging (Python pytest focus)

**Setup: launch.json for pytest**

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "debugpy",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "justMyCode": true
    },
    {
      "name": "Python: pytest (Current File)",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": [
        "${file}",
        "-v",
        "-s"
      ],
      "console": "integratedTerminal",
      "justMyCode": true
    },
    {
      "name": "Python: pytest (All)",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": [
        "tests/",
        "-v",
        "-s",
        "--tb=short"
      ],
      "console": "integratedTerminal",
      "justMyCode": true
    },
    {
      "name": "Python: pytest (Failed)",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": [
        "--lf",
        "-v",
        "-s"
      ],
      "console": "integratedTerminal"
    },
    {
      "name": "Rust: Debug Current File",
      "type": "lldb",
      "request": "launch",
      "program": "${workspaceFolder}/target/debug/${workspaceFolderBasename}",
      "args": [],
      "cwd": "${workspaceFolder}",
      "sourceLanguages": ["rust"]
    },
    {
      "name": "Go: Debug Current File",
      "type": "go",
      "request": "launch",
      "mode": "debug",
      "program": "${file}"
    },
    {
      "name": "Node: Debug TypeScript",
      "type": "node",
      "request": "launch",
      "runtimeArgs": ["-r", "ts-node/register"],
      "args": ["${file}"],
      "cwd": "${workspaceFolder}",
      "protocol": "inspector"
    }
  ]
}
```

**Debug Workflow:**

```bash
# 1. SET BREAKPOINTS
Click left gutter OR F9 on line
Red dot appears

# 2. CONDITIONAL BREAKPOINTS
Right-click breakpoint → Edit → Add condition
Example: "i > 10" or "user.name == 'admin'"

# 3. LOGPOINTS (print without code changes)
Right-click gutter → Add Logpoint
Example: "User: {user.name}, ID: {user.id}"

# 4. START DEBUG SESSION
F5 OR Debug panel → Select config → Start

# 5. DEBUG SPECIFIC TEST
Open test file → Click "Debug Test" above test function
Or: Ctrl+Shift+P → "Python: Debug Test Method"

# 6. STEP THROUGH CODE
F10  = Step Over (next line)
F11  = Step Into (enter function)
Shift+F11 = Step Out (exit function)
F5   = Continue to next breakpoint

# 7. INSPECT VARIABLES
Hover over variables
Check VARIABLES panel in sidebar
Add to WATCH panel for tracking

# 8. DEBUG CONSOLE
Evaluate expressions while paused
Example: type "len(data)" to check value

# 9. EXCEPTION BREAKPOINTS
Debug panel → Breakpoints section
Check "Raised Exceptions" or "Uncaught Exceptions"

# 10. POST-MORTEM DEBUGGING
When test fails, check CALL STACK panel
Click frames to see variable states
```

**Example: Debug failing pytest test**

```python
# tests/test_user.py
def test_user_creation():
    user = create_user("john", "doe")  # Set breakpoint here (F9)
    assert user.full_name == "John Doe"
    assert user.email is not None  # Fails here

# Workflow:
# 1. Click left of line 2 → Set breakpoint
# 2. F5 → Select "Python: pytest (Current File)"
# 3. Code pauses at breakpoint
# 4. Hover over 'user' to inspect
# 5. F10 to step to assertion
# 6. Debug Console: type 'user.email' to check value
# 7. Identify issue: email wasn't set in create_user()
```

---

## 5. Complete IntelliSense Configuration Guide

### Core IntelliSense Settings Explained

```json
{
  // Controls when suggestions appear automatically
  "editor.quickSuggestions": {
    "other": "on",        // Regular code (variables, functions)
    "comments": "off",    // Inside comments (usually off)
    "strings": "on"       // Inside strings (useful for paths, SQL)
  },
  
  // Trigger suggestions when typing special characters (., ::, ->)
  "editor.suggestOnTriggerCharacters": true,
  
  // Accept suggestion with characters like ., (, [
  "editor.acceptSuggestionOnCommitCharacter": true,
  
  // Accept with Enter key
  "editor.acceptSuggestionOnEnter": "on",  // or "smart" or "off"
  
  // Which suggestion is selected by default
  "editor.suggestSelection": "first",  // or "recentlyUsed" or "recentlyUsedByPrefix"
  
  // Snippet positioning in suggestion list
  "editor.snippetSuggestions": "top",  // or "bottom" or "inline" or "none"
  
  // Show preview of suggestion
  "editor.suggest.preview": true,
  
  // Don't suggest words from file
  "editor.suggest.showWords": false,
  
  // Prioritize suggestions from nearby code
  "editor.suggest.localityBonus": true,
  
  // Inline AI suggestions (Copilot)
  "editor.inlineSuggest.enabled": true,
  "editor.inlineSuggest.showToolbar": "onHover",
  
  // Parameter hints (function signatures)
  "editor.parameterHints.enabled": true,
  "editor.parameterHints.cycle": true,
  
  // Hover information
  "editor.hover.enabled": true,
  "editor.hover.delay": 300,  // milliseconds before hover appears
  "editor.hover.sticky": true  // Hover stays when moving mouse into it
}
```

### Language Server Configuration

**Python (Pylance)**
```json
{
  "python.languageServer": "Pylance",
  "python.analysis.autoImportCompletions": true,
  "python.analysis.completeFunctionParens": true,
  "python.analysis.typeCheckingMode": "basic",
  
  // Performance tuning
  "python.analysis.indexing": true,
  "python.analysis.diagnosticMode": "workspace",
  "python.analysis.autoSearchPaths": true,
  
  // Advanced completions
  "python.analysis.importFormat": "absolute",
  "python.analysis.completeFunctionParens": true,
  "python.analysis.autoFormatStrings": true
}
```

**Rust (rust-analyzer)**
```json
{
  "rust-analyzer.completion.autoimport.enable": true,
  "rust-analyzer.completion.autoself.enable": true,
  "rust-analyzer.completion.postfix.enable": true,
  "rust-analyzer.completion.privateEditable.enable": true,
  "rust-analyzer.completion.callable.snippets": "fill_arguments"
}
```

**Go (gopls)**
```json
{
  "go.useLanguageServer": true,
  "gopls": {
    "ui.completion.usePlaceholders": true,
    "ui.completion.completionBudget": "100ms",
    "ui.completion.matcher": "fuzzy",
    "completeUnimported": true,
    "deepCompletion": true
  }
}
```

**TypeScript**
```json
{
  "typescript.suggest.autoImports": true,
  "typescript.suggest.completeFunctionCalls": true,
  "typescript.suggest.includeAutomaticOptionalChainCompletions": true,
  "typescript.preferences.includePackageJsonAutoImports": "auto"
}
```

### Essential Keyboard Shortcuts

```json
// keybindings.json (Ctrl+K Ctrl+S → Open Keyboard Shortcuts)
[
  {
    "key": "ctrl+space",
    "command": "editor.action.triggerSuggest",
    "when": "editorHasCompletionItemProvider && textInputFocus && !editorReadonly"
  },
  {
    "key": "tab",
    "command": "editor.action.inlineSuggest.commit",
    "when": "inlineSuggestionVisible && !editorTabMovesFocus"
  },
  {
    "key": "ctrl+right",
    "command": "editor.action.inlineSuggest.acceptNextWord",
    "when": "inlineSuggestionVisible"
  },
  {
    "key": "alt+]",
    "command": "editor.action.inlineSuggest.showNext",
    "when": "inlineSuggestionVisible"
  },
  {
    "key": "alt+[",
    "command": "editor.action.inlineSuggest.showPrevious",
    "when": "inlineSuggestionVisible"
  },
  ```

```json
  {
    "key": "ctrl+shift+space",
    "command": "editor.action.triggerParameterHints",
    "when": "editorHasSignatureHelpProvider && editorTextFocus"
  },
  {
    "key": "ctrl+i",
    "command": "editor.action.showHover",
    "when": "editorTextFocus"
  },
  {
    "key": "ctrl+.",
    "command": "editor.action.quickFix",
    "when": "editorHasCodeActionsProvider && editorTextFocus"
  },
  {
    "key": "ctrl+k ctrl+i",
    "command": "editor.action.showHover",
    "when": "editorTextFocus"
  },
  // Navigate through suggestion list
  {
    "key": "ctrl+n",
    "command": "selectNextSuggestion",
    "when": "suggestWidgetMultipleSuggestions && suggestWidgetVisible"
  },
  {
    "key": "ctrl+p",
    "command": "selectPrevSuggestion",
    "when": "suggestWidgetMultipleSuggestions && suggestWidgetVisible"
  },
  // Cycle through parameter hints
  {
    "key": "alt+up",
    "command": "showPrevParameterHint",
    "when": "parameterHintsVisible"
  },
  {
    "key": "alt+down",
    "command": "showNextParameterHint",
    "when": "parameterHintsVisible"
  },
  // Accept suggestion without replacing
  {
    "key": "ctrl+enter",
    "command": "acceptSelectedSuggestion",
    "when": "suggestWidgetVisible"
  }
]
```

### Troubleshooting Checklist

**When suggestions don't appear:**

```bash
# 1. CHECK LANGUAGE SERVER STATUS
Bottom bar → Click language indicator (e.g., "Python", "Rust Analyzer")
Look for errors or "Starting..." status

# 2. VERIFY EXTENSION IS ACTIVE
Ctrl+Shift+X → Search for language extension
Ensure it's enabled and up to date

# 3. RELOAD WINDOW
Ctrl+Shift+P → "Developer: Reload Window"

# 4. CHECK OUTPUT PANEL
Ctrl+Shift+U → Select language server from dropdown
Look for error messages

# 5. VERIFY SETTINGS
Ctrl+, → Search "quickSuggestions"
Ensure it's not set to "off"

# 6. CHECK FILE ASSOCIATION
Bottom right → Click language mode
Ensure correct language is selected

# 7. WORKSPACE INDEXING
For Python: Check if .venv is activated
For Rust: Ensure Cargo.toml exists
For Go: Check go.mod is present
For TypeScript: Verify tsconfig.json exists

# 8. CLEAR LANGUAGE SERVER CACHE
# Python
Ctrl+Shift+P → "Python: Clear Cache and Reload Window"

# Rust
Delete target/ folder, restart rust-analyzer

# Go
Ctrl+Shift+P → "Go: Reset Go Tools Cache"

# TypeScript
Delete node_modules/.cache, restart TS server

# 9. CHECK WORKSPACE SETTINGS
.vscode/settings.json might override user settings
Review for conflicts

# 10. VERBOSE LOGGING
# Add to settings.json for debugging:
"rust-analyzer.trace.server": "verbose",
"python.analysis.logLevel": "Trace",
"go.languageServerFlags": ["-rpc.trace"],
"typescript.tsserver.log": "verbose"

# Then check Output panel for detailed logs
```

### Three Example Scenarios

#### Scenario 1: Accepting Multi-line Inline Suggestions

**Situation:** Copilot suggests a complete function implementation

```python
# You type:
def calculate_fibonacci(n: int) -> list[int]:
    """Calculate fibonacci sequence up to n terms."""
    # [Copilot suggests multiple lines here shown in gray]
    # result = []
    # a, b = 0, 1
    # for _ in range(n):
    #     result.append(a)
    #     a, b = b, a + b
    # return result

# Actions:
# 1. Tab → Accept entire suggestion
# 2. Ctrl+→ → Accept only next word ("result")
# 3. Alt+] → See alternative suggestions
# 4. Esc → Dismiss suggestion entirely

# Pro tip: Use Ctrl+→ multiple times to accept word-by-word
# This lets you modify as you accept
```

**Configuration for better inline suggestions:**
```json
{
  "editor.inlineSuggest.enabled": true,
  "github.copilot.editor.enableAutoCompletions": true,
  "github.copilot.enable": {
    "*": true,
    "yaml": false,
    "plaintext": false
  }
}
```

#### Scenario 2: Converting Suggestion into Reusable Snippet

**Situation:** You frequently write the same boilerplate code

```python
# You keep typing this pattern:
@pytest.fixture
def temp_file():
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        yield f.name
    os.unlink(f.name)

# Convert to snippet:
# 1. Ctrl+Shift+P → "Configure User Snippets"
# 2. Select "python.json"
# 3. Add snippet:
```

```json
{
  "Pytest Temp File Fixture": {
    "prefix": "fix-temp",
    "body": [
      "@pytest.fixture",
      "def ${1:temp_file}():",
      "    with tempfile.NamedTemporaryFile(mode='${2:w}', delete=False) as f:",
      "        yield f.name",
      "    os.unlink(f.name)$0"
    ],
    "description": "Create a temporary file fixture with automatic cleanup"
  },
  
  "Rust Result Match": {
    "prefix": "match-result",
    "body": [
      "match ${1:result} {",
      "    Ok(${2:value}) => ${3:value},",
      "    Err(${4:err}) => {",
      "        eprintln!(\"Error: {}\", ${4:err});",
      "        return Err(${4:err}.into());",
      "    }",
      "}$0"
    ],
    "description": "Match on Result with error handling"
  },
  
  "Go Error Check": {
    "prefix": "iferr",
    "body": [
      "if err != nil {",
      "    return ${1:nil, }fmt.Errorf(\"${2:operation failed}: %w\", err)",
      "}$0"
    ],
    "description": "Standard Go error check with wrapped error"
  },
  
  "TypeScript React Component": {
    "prefix": "rfc",
    "body": [
      "interface ${1:Component}Props {",
      "    ${2:prop}: ${3:string};",
      "}",
      "",
      "export const ${1:Component}: React.FC<${1:Component}Props> = ({ ${2:prop} }) => {",
      "    return (",
      "        <div>",
      "            ${0}",
      "        </div>",
      "    );",
      "};"
    ],
    "description": "React functional component with TypeScript"
  }
}
```

**Using snippets:**
```bash
# 1. Type prefix: "fix-temp"
# 2. IntelliSense shows snippet in dropdown
# 3. Tab to accept
# 4. Tab to jump between placeholders ($1, $2, $3)
# 5. Esc to exit snippet mode

# Snippet navigation:
Tab → Next placeholder
Shift+Tab → Previous placeholder
```

**Creating snippet from selected code:**
```bash
# Method 1: Manual
# 1. Select code
# 2. Ctrl+Shift+P → "Configure User Snippets"
# 3. Paste code into "body" array, add ${1:placeholder} markers

# Method 2: Using extension
# Install: "Easy Snippet Maker" extension
# 1. Select code
# 2. Ctrl+Shift+P → "Easy Snippet: Make Snippet"
# 3. Enter prefix and description
```

#### Scenario 3: Disabling Noisy Suggestions

**Situation:** Too many irrelevant suggestions slow you down

```json
{
  // Disable word-based suggestions (only show semantic)
  "editor.suggest.showWords": false,
  "editor.wordBasedSuggestions": "off",
  
  // Reduce suggestion delay
  "editor.quickSuggestionsDelay": 10,  // milliseconds
  
  // Only show top 10 suggestions
  "editor.suggest.maxVisibleSuggestions": 10,
  
  // Filter by typing
  "editor.suggest.filterGraceful": true,
  
  // Language-specific filtering
  "[python]": {
    "editor.suggest.showModules": true,
    "editor.suggest.showClasses": true,
    "editor.suggest.showFunctions": true,
    "editor.suggest.showVariables": true,
    "editor.suggest.showKeywords": false  // If too noisy
  },
  
  // Disable specific suggestion sources
  "python.analysis.completeFunctionParens": false,  // Don't add () automatically
  "typescript.suggest.completeFunctionCalls": false,
  
  // Disable inline suggestions in specific contexts
  "github.copilot.enable": {
    "markdown": false,  // No suggestions in markdown
    "yaml": false,      // No suggestions in config files
    "json": false
  },
  
  // Per-language inline suggestions
  "[rust]": {
    "editor.inlineSuggest.enabled": true  // Enable for Rust
  },
  "[markdown]": {
    "editor.inlineSuggest.enabled": false  // Disable for Markdown
  },
  
  // Reduce Pylance noise
  "python.analysis.diagnosticSeverityOverrides": {
    "reportUnusedImport": "information",
    "reportUnusedVariable": "information",
    "reportMissingTypeStubs": "none"
  },
  
  // Reduce rust-analyzer noise
  "rust-analyzer.diagnostics.disabled": [
    "unresolved-proc-macro",
    "missing-unsafe"
  ],
  
  // Reduce gopls noise
  "gopls": {
    "analyses": {
      "unusedparams": false,
      "shadow": false
    }
  }
}
```

**Quick toggles (add to keybindings.json):**
```json
[
  {
    "key": "ctrl+alt+i",
    "command": "toggleSuggestionDetails",
    "when": "suggestWidgetVisible"
  },
  {
    "key": "ctrl+alt+s",
    "command": "workbench.action.toggleInlineSuggest"
  }
]
```

---

## 6. MCP (Model Context Protocol) Server Integration

### Setting up MCP Documentation Server

**Install MCP Server for Documentation:**

```bash
# Install MCP CLI
npm install -g @modelcontextprotocol/cli

# Create MCP server configuration
mkdir -p ~/.config/mcp
```

**MCP Server Configuration (~/.config/mcp/config.json):**

```json
{
  "mcpServers": {
    "docs": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-docs"
      ],
      "env": {
        "DOCS_PATH": "/path/to/your/docs"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "${workspaceFolder}"
      ]
    },
    "git": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-git"
      ]
    }
  }
}
```

**VSCode Integration with MCP:**

```json
// settings.json
{
  "mcp.servers": [
    {
      "name": "documentation",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-docs"],
      "env": {
        "DOCS_PATH": "${workspaceFolder}/docs"
      }
    }
  ],
  
  // Use MCP for enhanced completions
  "mcp.enableCompletions": true,
  "mcp.enableHover": true,
  "mcp.enableDefinitions": true
}
```

**Using MCP Documentation in Workflow:**

```bash
# 1. QUERY DOCUMENTATION
Ctrl+Shift+P → "MCP: Query Documentation"
Type: "How to use async/await in Rust"
→ Returns context-aware documentation

# 2. INLINE DOCUMENTATION HINTS
Hover over function → Shows MCP-enhanced documentation
Including examples from your team's codebase

# 3. CONTEXT-AWARE COMPLETIONS
Start typing function → MCP provides completions
Based on your project's documentation and patterns

# 4. SEARCH PROJECT DOCUMENTATION
Ctrl+Shift+P → "MCP: Search Project Docs"
Searches across README, wiki, internal docs
```

---

## 7. Advanced Tips & Tricks

### Tip 1: Multi-Cursor Magic

```bash
# PATTERN: Edit multiple similar lines simultaneously

# Method 1: Column selection
Alt+Shift+Drag → Select rectangular region
Type to edit all lines

# Method 2: Add cursor above/below
Ctrl+Alt+Up/Down → Add cursor on adjacent lines

# Method 3: Select all occurrences
Ctrl+D → Select next occurrence
Ctrl+Shift+L → Select ALL occurrences
Type to change all

# Method 4: Manual cursor placement
Alt+Click → Place cursor at each click location

# Example use case:
# Before:
user_name = "john"
user_email = "john@example.com"
user_age = 30

# Place cursor on each "user_", Ctrl+D three times
# Type "customer_" → All replaced simultaneously
```

### Tip 2: Workspace-Specific Settings

```bash
# Create .vscode/settings.json in project root
# Overrides user settings for this workspace only

# Example: Project uses 2-space indentation
{
  "editor.tabSize": 2,
  "python.testing.pytestArgs": [
    "tests",
    "--cov=src",
    "--cov-report=html"
  ],
  "python.analysis.extraPaths": [
    "./src",
    "./lib"
  ]
}
```

### Tip 3: Tasks for Common Operations

**Create .vscode/tasks.json:**

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Python: Run Tests with Coverage",
      "type": "shell",
      "command": "pytest",
      "args": [
        "tests/",
        "--cov=src",
        "--cov-report=html",
        "-v"
      ],
      "group": "test",
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "Rust: Check All",
      "type": "shell",
      "command": "cargo",
      "args": ["check", "--all-targets"],
      "group": "build",
      "problemMatcher": "$rustc"
    },
    {
      "label": "Rust: Clippy Fix",
      "type": "shell",
      "command": "cargo",
      "args": ["clippy", "--fix", "--allow-dirty"],
      "group": "build"
    },
    {
      "label": "Go: Test with Race Detector",
      "type": "shell",
      "command": "go",
      "args": ["test", "-race", "-v", "./..."],
      "group": "test",
      "problemMatcher": "$go"
    },
    {
      "label": "TypeScript: Build Watch",
      "type": "shell",
      "command": "npm",
      "args": ["run", "build", "--", "--watch"],
      "group": "build",
      "isBackground": true
    },
    {
      "label": "Format All Files",
      "type": "shell",
      "command": "prettier",
      "args": ["--write", "**/*.{ts,tsx,js,jsx,json,md}"],
      "group": "build"
    }
  ]
}
```

**Run tasks:**
```bash
Ctrl+Shift+P → "Tasks: Run Task"
Or bind to keyboard shortcut in keybindings.json
```

### Tip 4: Code Snippets with Dynamic Variables

```json
{
  "Python Test with Datetime": {
    "prefix": "test-date",
    "body": [
      "def test_${1:function_name}_${CURRENT_YEAR}${CURRENT_MONTH}${CURRENT_DATE}():",
      "    \"\"\"Test ${1:function_name} on $CURRENT_MONTH_NAME $CURRENT_DATE, $CURRENT_YEAR\"\"\"",
      "    # Arrange",
      "    ${2:input_data} = ${3:None}",
      "    ",
      "    # Act",
      "    result = ${1:function_name}(${2:input_data})",
      "    ",
      "    # Assert",
      "    assert result == ${4:expected}$0"
    ]
  }
}
```

**Available snippet variables:**
```
$CURRENT_YEAR               2025
$CURRENT_MONTH              10
$CURRENT_DATE               06
$CURRENT_HOUR               14
$CURRENT_MINUTE             30
$CURRENT_SECOND             45
$CURRENT_DAY_NAME           Monday
$CURRENT_MONTH_NAME         October
$TM_FILENAME                current_file.py
$TM_FILENAME_BASE           current_file
$TM_DIRECTORY               /path/to/directory
$TM_FILEPATH                /path/to/current_file.py
$CLIPBOARD                  clipboard contents
$WORKSPACE_NAME             project-name
$WORKSPACE_FOLDER           /path/to/workspace
$RANDOM                     6 random digits
$RANDOM_HEX                 6 random hex
$UUID                       UUID v4
$LINE_COMMENT               # (language-specific)
$BLOCK_COMMENT_START        """ (language-specific)
$BLOCK_COMMENT_END          """
```

### Tip 5: Zen Mode for Focus

```bash
# Enter distraction-free coding
Ctrl+K Z → Zen Mode

# Configure Zen Mode
{
  "zenMode.hideLineNumbers": false,
  "zenMode.hideTabs": true,
  "zenMode.hideStatusBar": false,
  "zenMode.hideActivityBar": true,
  "zenMode.centerLayout": true,
  "zenMode.fullScreen": false,
  "zenMode.restore": true  // Restore on reload
}

# Exit Zen Mode
Esc Esc (press Esc twice)
```

### Tip 6: Project Templates with Snippets

**Create project scaffolding:**

```bash
# Install extension
ext install yzhang.markdown-all-in-one

# Or use built-in template feature
Ctrl+Shift+P → "File: New File from Template"
```

**Custom Python project template:**

```python
# Save as ~/.config/Code/User/templates/python_project.py
"""
${1:Module Name}

Description: ${2:Brief description}
Author: ${3:Your Name}
Date: $CURRENT_YEAR-$CURRENT_MONTH-$CURRENT_DATE
"""

from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point."""
    ${0:pass}


if __name__ == "__main__":
    main()
```

### Tip 7: Git Integration Shortcuts

```bash
# Stage current file
Ctrl+Shift+P → "Git: Stage Changes"

# Commit with message
Ctrl+Shift+P → "Git: Commit"

# Quick diff view
Ctrl+Shift+P → "Git: Open Changes"
Or click file in Source Control panel

# Time travel through file history
Ctrl+Shift+P → "Git: View File History"
(Requires GitLens extension)

# Blame current line
Ctrl+Shift+P → "Git: Toggle Line Blame"

# Compare with branch
Ctrl+Shift+P → "Git: Compare with Branch"
```

### Tip 8: Remote Development

```bash
# SSH into remote machine
Ctrl+Shift+P → "Remote-SSH: Connect to Host"

# Open folder on remote
File → Open Folder → Select remote path

# Extensions install automatically on remote
# Develop as if local, but code runs remotely

# Pro tip: Add to ~/.ssh/config
Host devserver
    HostName 192.168.1.100
    User developer
    IdentityFile ~/.ssh/id_rsa
    ForwardAgent yes
```

### Tip 9: Custom Language Injections

**Syntax highlighting in multi-language files:**

```json
{
  "editor.tokenColorCustomizations": {
    "textMateRules": [
      {
        "scope": "string.quoted.double.python",
        "settings": {
          "foreground": "#CE9178"
        }
      }
    ]
  },
  
  // SQL highlighting in Python strings
  "python.analysis.autoFormatStrings": true,
  
  // Markdown in Python docstrings
  "python.analysis.inlayHints.pytestParameters": true
}
```

### Tip 10: Performance Optimization

```json
{
  // Exclude large folders from file watching
  "files.watcherExclude": {
    "**/.git/objects/**": true,
    "**/.git/subtree-cache/**": true,
    "**/node_modules/**": true,
    "**/target/**": true,
    "**/.venv/**": true,
    "**/venv/**": true,
    "**/__pycache__/**": true,
    "**/dist/**": true,
    "**/build/**": true
  },
  
  // Reduce file search scope
  "search.exclude": {
    "**/node_modules": true,
    "**/bower_components": true,
    "**/*.code-search": true,
    "**/target": true,
    "**/.venv": true
  },
  
  // Limit file size for features
  "editor.largeFileOptimizations": true,
  "files.maxMemoryForLargeFilesMB": 4096,
  
  // Disable unused features
  "editor.codeLens": false,  // If you don't use it
  "editor.lightbulb.enabled": false,  // If too distracting
  
  // Reduce Git status checks
  "git.autorefresh": false,
  "git.autofetch": false,
  
  // TypeScript performance
  "typescript.disableAutomaticTypeAcquisition": false,
  "typescript.tsserver.maxTsServerMemory": 4096
}
```

---

## 8. Quick Reference Card

**Print this and keep near your desk:**

```
═══════════════════════════════════════════════════════════
  VSCODE ESSENTIAL SHORTCUTS - QUICK REFERENCE
═══════════════════════════════════════════════════════════

NAVIGATION                  | CODE EDITING
Ctrl+P      Open file       | Ctrl+Space    Trigger suggestions
Ctrl+Shift+O Go to symbol   | Ctrl+.        Quick fix
Ctrl+T      Workspace symbol| F2            Rename
Ctrl+G      Go to line      | Ctrl+/        Comment line
F12         Go to definition| Ctrl+D        Select occurrence
Alt+F12     Peek definition | Ctrl+Shift+L  Select all occur.
Shift+F12   Find references | Alt+Up/Down   Move line

INLINE SUGGESTIONS          | DEBUGGING
Tab         Accept          | F5            Start debug
Ctrl+→      Accept word     | F9            Breakpoint
Alt+]       Next suggestion | F10           Step over
Alt+[       Prev suggestion | F11           Step into
Esc         Dismiss         | Shift+F11     Step out

TERMINAL & VIEWS            | SEARCH
Ctrl+`      Toggle terminal | Ctrl+F        Find
Ctrl+B      Toggle sidebar  | Ctrl+Shift+F  Find in files
Ctrl+J      Toggle panel    | Ctrl+H        Replace
Ctrl+\      Split editor    | F3            Find next

═══════════════════════════════════════════════════════════
```

---

## Summary Checklist

- [ ] Copy settings.json to `~/.config/Code/User/settings.json`
- [ ] Install essential extensions for your languages
- [ ] Configure language servers (Pylance, rust-analyzer, gopls)
- [ ] Set up launch.json for debugging
- [ ] Create tasks.json for common operations
- [ ] Add custom snippets for frequent patterns
- [ ] Configure keybindings.json for preferred shortcuts
- [ ] Set up MCP server if using documentation integration
- [ ] Optimize performance settings for large projects
- [ ] Test IntelliSense, inline suggestions, and debugging

**Next steps:** Practice the three workflows daily for one week to build muscle memory. The keyboard shortcuts will become second nature within 2-3 weeks of consistent use.

Let me help you find information about getting appropriate suggestions in Visual Studio Code. I'll search for accurate and up-to-date information about this topic.Let me help you understand how to effectively use suggestions in Visual Studio Code (VSCode). Based on the search results, here are the key ways to get better code suggestions:

1. **Basic Shortcuts for Suggestions**:
   - Press `Ctrl+Space` (Windows/Linux) or `Cmd+Space` (Mac) to manually trigger suggestions at any time
   - This is especially useful when automatic suggestions don't appear or you want to see all available options

2. **Configure IntelliSense Settings**:
   - Open Settings (`Ctrl+,` or `Cmd+,`)
   - Search for "quick suggestions"
   - You can customize when and how suggestions appear:
     - Inline suggestions (shows directly in your code)
     - Widget suggestions (shows in a popup box)
     - Language-specific settings

3. **Helpful Features**:
   - Parameter hints will show up automatically when typing function calls
   - Member lists appear when typing a dot (.) after an object
   - Documentation hover: hover over any symbol to see its documentation
   - Snippets: pre-made code templates that appear in suggestions

4. **Tips for Better Suggestions**:
   - Install relevant extensions for your programming languages
   - Keep your VSCode and extensions updated
   - Use proper file extensions (e.g., `.js` for JavaScript) to get language-specific suggestions
   - Write cleaner code with proper syntax to improve suggestion accuracy

5. **Keyboard Shortcuts for Navigation**:
   - `↑` and `↓` arrows to navigate through suggestions
   - `Enter` or `Tab` to accept a suggestion
   - `Esc` to dismiss suggestions
   - `F2` for renaming symbols across your project

6. **Customization Options**:
   You can modify settings in `settings.json`:
   ```json
   {
     "editor.suggestSelection": "first",
     "editor.quickSuggestions": {
       "other": true,
       "comments": false,
       "strings": false
     },
     "editor.acceptSuggestionOnEnter": "on",
     "editor.snippetSuggestions": "top"
   }
   ```

7. **Language-Specific Intelligence**:
   - Install language servers and extensions for better language-specific suggestions
   - Popular extensions like Python, JavaScript/TypeScript, and Java extensions provide enhanced IntelliSense support

8. **Troubleshooting Tips**:
   If suggestions aren't working well:
   - Check if the appropriate language extension is installed
   - Reload VSCode (`Ctrl+Shift+P` or `Cmd+Shift+P`, then type "Reload Window")
   - Verify file type is correctly recognized (check bottom-right corner of VSCode)
   - Clear the IntelliSense cache if needed

Would you like me to explain any of these features in more detail or help you with setting up suggestions for a specific programming language?