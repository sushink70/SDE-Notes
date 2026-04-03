Here's a complete guide to setting up and using **GoNB** on Ubuntu Linux with VSCode.

---

## 🐧 Step 1 — Full Ubuntu Setup

### 1. Install Go (if not already installed)

```bash
sudo apt update && sudo apt install -y golang-go
# Or install the latest version manually:
# https://go.dev/dl/
```

Verify: `go version`

### 2. Install Jupyter

```bash
sudo apt install -y python3-pip
pip3 install jupyterlab notebook
```

### 3. Install GoNB + required tools

Run the following to install GoNB, `goimports`, and `gopls` (needed for auto-complete) into your `GOBIN` directory:

```bash
go install github.com/janpfeifer/gonb@latest && \
  go install golang.org/x/tools/cmd/goimports@latest && \
  go install golang.org/x/tools/gopls@latest
```

### 4. Add GOBIN to your PATH

```bash
# Add this to your ~/.bashrc or ~/.zshrc:
export PATH=$PATH:$(go env GOPATH)/bin

# Then reload:
source ~/.bashrc
```

### 5. Register GoNB as a Jupyter kernel

```bash
gonb --install
```

This registers GoNB for both JupyterLab and classic Jupyter Notebook.

### 6. Start Jupyter

```bash
jupyter lab
# or
jupyter notebook
```

---

## 📓 Step 2 — Running Go Code in a Notebook

Once Jupyter is open, create a new notebook and select the **Go (gonb)** kernel.

The key special syntax is `%%` — it is a special GoNB command that means "insert a `func main() {...}` here." Without it, you're just writing package-level declarations.

**Basic example cell:**

```go
import "fmt"

%%
fmt.Println("Hello from Go in Jupyter!")
```

**Other useful cell magic commands:**

| Command | What it does |
|---|---|
| `%%` | Wraps code in `func main()` and runs it |
| `%help` | Shows all available GoNB commands |
| `!<cmd>` | Run a shell command (e.g. `!go get ...`) |
| `%test` | Runs `Test*` / `Benchmark*` functions with `go test` |

---

## 🖥️ Step 3 — Selecting the GoNB Kernel in VSCode

### Prerequisites
Install the **Jupyter extension** in VSCode (by Microsoft).

### How to select the kernel:

VSCode can open GoNB notebooks as a normal tab. When opening a `.ipynb` file it will ask which kernel to use, and if GoNB is installed it will offer it as an option.

1. Open (or create) a `.ipynb` file in VSCode
2. Click the **kernel selector** in the top-right corner of the notebook (it may say "Select Kernel" or show a Python version)
3. Choose **"Jupyter Kernel..."** → then pick **Go (gonb)** from the list
4. If it doesn't appear, make sure `gonb --install` was run and restart VSCode

### ⚠️ VSCode Caveats to Know

VSCode doesn't use Jupyter's completion protocol, so it won't offer GoNB's auto-complete or contextual help (which is powered by `gopls`). For that, use JupyterLab in the browser instead.

VSCode also does not render the `text/javascript` mimetype properly — it just displays it as text — so widget-based UI and some Plotly versions won't work in VSCode.

---

## 🐳 Alternative: Docker (quickest way to try it)

GoNB offers a pre-built Docker image with JupyterLab included. Run it like this:

```bash
docker pull janpfeifer/gonb_jupyterlab:latest
docker run -it --rm -p 8888:8888 -v "${PWD}":/notebooks janpfeifer/gonb_jupyterlab:latest
```

Then open the URL it prints in your browser — no installation needed.

---

## Summary Checklist

- [x] Go installed and `GOPATH/bin` in `PATH`
- [x] `gonb`, `goimports`, `gopls` installed via `go install`
- [x] `gonb --install` run to register the kernel
- [x] Jupyter started fresh after install
- [x] Use `%%` in cells to execute code
- [x] In VSCode, select kernel from top-right → "Go (gonb)"