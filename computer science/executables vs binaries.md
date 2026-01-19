# Executables vs. Binaries: The Complete Mental Model

This is a **foundational systems concept** that most programmers misunderstand. Let's build precise mental models.

---

## **The Core Distinction**

### **Binary (Broader Term)**
A **binary file** is any file containing **non-textual data** (i.e., not human-readable text). The term comes from the fact that the file contains raw **binary data** (sequences of bytes in base-2 representation).

### **Executable (Specific Type)**
An **executable** is a **specific type of binary** that the operating system can **load and run as a process**.

### **The Relationship:**
```
┌─────────────────────────────────────┐
│         All Files                   │
│  ┌──────────────────────────────┐   │
│  │     Binary Files             │   │
│  │  ┌────────────────────────┐  │   │
│  │  │   Executable Files     │  │   │
│  │  │  (Runnable Programs)   │  │   │
│  │  └────────────────────────┘  │   │
│  │                              │   │
│  │  Other binaries:             │   │
│  │  • Libraries (.so, .dll)     │   │
│  │  • Object files (.o)         │   │
│  │  • Images (.png, .jpg)       │   │
│  │  • Videos (.mp4)             │   │
│  └──────────────────────────────┘   │
│                                     │
│  Text Files:                        │
│  • Source code (.c, .rs, .go)       │
│  • Config files (.json, .toml)      │
└─────────────────────────────────────┘
```

**Key Insight:** All executables are binaries, but **not all binaries are executables**.

---

## **Comprehensive Classification**

### **1. Text Files (Human-Readable)**
```bash
$ cat hello.c
#include <stdio.h>
int main() {
    printf("Hello\n");
    return 0;
}
```
- **Encoding:** UTF-8, ASCII, etc.
- **Readable:** Yes, with a text editor
- **Executable:** No (needs compilation first)

---

### **2. Binary Files (Machine-Readable)**

All of these contain **raw bytes**, not text:

#### **2a. Executable Binaries (Can Run)**

**Linux/Unix:**
```bash
$ file /bin/ls
/bin/ls: ELF 64-bit LSB executable, x86-64

$ ./a.out
Hello, World!
```

**Windows:**
```cmd
> file notepad.exe
notepad.exe: PE32+ executable (GUI) x86-64

> notepad.exe
[Notepad launches]
```

**macOS:**
```bash
$ file /bin/ls
/bin/ls: Mach-O 64-bit executable x86_64
```

**Characteristics:**
- Contains **machine code** (CPU instructions)
- Has **entry point** (where execution starts)
- OS can **load it into memory** and create a process
- **Runnable** via `./program` (Unix) or double-click (GUI)

---

#### **2b. Non-Executable Binaries (Cannot Run Directly)**

##### **Object Files (.o, .obj)**
Compiled but **not linked**:

```bash
# Compile without linking
$ gcc -c hello.c -o hello.o

$ file hello.o
hello.o: ELF 64-bit LSB relocatable, x86-64

$ ./hello.o
bash: ./hello.o: cannot execute binary file
```

**Why not executable?**
- Missing **entry point** (`main`)
- Contains **unresolved symbols** (function references)
- Needs **linking** to become executable

---

##### **Shared Libraries (.so, .dll, .dylib)**

**Linux:**
```bash
$ file /lib/x86_64-linux-gnu/libc.so.6
libc.so.6: ELF 64-bit LSB shared object, x86-64

$ ./libc.so.6  # Some .so files can run for diagnostics
```

**Windows:**
```cmd
> file C:\Windows\System32\kernel32.dll
kernel32.dll: PE32+ executable (DLL) x86-64
```

**Characteristics:**
- Contains **compiled code**
- **No main()** entry point (usually)
- **Loaded by other programs** at runtime
- **Cannot run standalone** (but can be loaded by OS)

---

##### **Static Libraries (.a, .lib)**

Archives of object files:

```bash
$ ar rcs libmath.a add.o subtract.o

$ file libmath.a
libmath.a: current ar archive

$ ./libmath.a
bash: ./libmath.a: cannot execute binary file
```

**Purpose:** Bundled into executables **at link time** (not runtime).

---

##### **Media Files (Images, Videos, Audio)**

```bash
$ file image.png
image.png: PNG image data, 1920 x 1080, 8-bit/color RGBA

$ file video.mp4
video.mp4: ISO Media, MP4 Base Media v1
```

**Why binary?**
- Compressed/encoded data
- Not CPU instructions
- Requires **decoder software** to interpret

---

##### **Data Files (Databases, Archives)**

```bash
$ file database.sqlite
database.sqlite: SQLite 3.x database

$ file archive.zip
archive.zip: Zip archive data
```

---

## **The Anatomy of an Executable**

Let's dissect what makes a binary **executable**:

### **ELF Format (Linux/Unix) - Detailed Breakdown**

```
┌─────────────────────────────────────────┐
│          ELF Header                     │  ← Magic number, architecture, entry point
├─────────────────────────────────────────┤
│       Program Headers                   │  ← How to load into memory
├─────────────────────────────────────────┤
│         .text Section                   │  ← Machine code (CPU instructions)
├─────────────────────────────────────────┤
│         .data Section                   │  ← Initialized global variables
├─────────────────────────────────────────┤
│         .bss Section                    │  ← Uninitialized global variables
├─────────────────────────────────────────┤
│        .rodata Section                  │  ← Read-only data (string literals)
├─────────────────────────────────────────┤
│       .symtab Section                   │  ← Symbol table (for debugging)
├─────────────────────────────────────────┤
│      Section Headers                    │  ← Metadata about sections
└─────────────────────────────────────────┘
```

**Inspect an executable:**

```bash
$ readelf -h /bin/ls
ELF Header:
  Magic:   7f 45 4c 46 02 01 01 00 00 00 00 00 00 00 00 00 
  Class:                             ELF64
  Entry point address:               0x6a30  ← Where execution starts!
  
$ objdump -d /bin/ls | head -20
0000000000006a30 <_start>:   ← The actual entry point
    6a30:	f3 0f 1e fa          	endbr64 
    6a34:	31 ed                	xor    %ebp,%ebp
    ...
```

---

### **PE Format (Windows) - Structure**

```
┌─────────────────────────────────────────┐
│         DOS Header                      │  ← Backward compatibility
├─────────────────────────────────────────┤
│         PE Header                       │  ← Magic "PE\0\0", architecture
├─────────────────────────────────────────┤
│       Optional Header                   │  ← Entry point, image base
├─────────────────────────────────────────┤
│       Section Table                     │  ← .text, .data, .rdata, etc.
├─────────────────────────────────────────┤
│       .text Section                     │  ← Code
├─────────────────────────────────────────┤
│       .data Section                     │  ← Data
├─────────────────────────────────────────┤
│      Import Table                       │  ← DLLs needed
├─────────────────────────────────────────┤
│      Export Table                       │  ← Functions exported (if DLL)
└─────────────────────────────────────────┘
```

---

## **The Compilation Pipeline: Text → Binary → Executable**

Let's trace a complete journey:

### **Example in C:**

```c
// hello.c (TEXT FILE)
#include <stdio.h>

int main() {
    printf("Hello, World!\n");
    return 0;
}
```

### **Step-by-Step Transformation:**

```bash
# 1. Preprocessing (still text)
$ gcc -E hello.c -o hello.i
# Expands #include, macros → hello.i (text file with 800+ lines)

# 2. Compilation (text → assembly)
$ gcc -S hello.c -o hello.s
# Generates assembly code → hello.s (text file)
$ cat hello.s
    .section .rodata
.LC0:
    .string "Hello, World!"
    .text
    .globl  main
main:
    pushq   %rbp
    movq    %rsp, %rbp
    leaq    .LC0(%rip), %rdi
    call    puts@PLT
    ...

# 3. Assembly (assembly → object file)
$ gcc -c hello.c -o hello.o
# Binary file, but NOT executable
$ file hello.o
hello.o: ELF 64-bit LSB relocatable, x86-64

$ xxd hello.o | head -5  # View raw bytes
00000000: 7f45 4c46 0201 0100 0000 0000 0000 0000  .ELF............
00000010: 0100 3e00 0100 0000 0000 0000 0000 0000  ..>.............

# 4. Linking (object file → executable)
$ gcc hello.o -o hello
# Now it's executable!
$ file hello
hello: ELF 64-bit LSB executable, x86-64

$ ./hello
Hello, World!
```

---

### **The Same in Rust:**

```rust
// main.rs (TEXT FILE)
fn main() {
    println!("Hello, World!");
}
```

```bash
# All steps in one (Rust hides complexity)
$ rustc main.rs -o hello

# But you can see intermediate steps
$ rustc --emit=llvm-ir main.rs    # → main.ll (LLVM IR, text)
$ rustc --emit=asm main.rs        # → main.s (assembly, text)
$ rustc --emit=obj main.rs        # → main.o (object file, binary)
$ rustc main.rs                   # → main (executable, binary)

$ file main
main: ELF 64-bit LSB pie executable, x86-64

$ ./main
Hello, World!
```

---

## **Key Differentiators: What Makes a Binary Executable?**

| Property | Text File | Object File (.o) | Library (.so/.dll) | Executable |
|----------|-----------|------------------|--------------------|--------------|
| **Human-readable** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Contains machine code** | ❌ No | ✅ Yes | ✅ Yes | ✅ Yes |
| **Has entry point** | ❌ No | ❌ No | Sometimes | ✅ Yes |
| **Runnable by OS** | ❌ No | ❌ No | ❌ No* | ✅ Yes |
| **Self-contained** | N/A | ❌ No | ❌ No | ✅ Yes** |

*Shared libraries can sometimes run for diagnostics  
**May still depend on other shared libraries

---

## **Practical Verification Commands**

### **Linux/Unix:**

```bash
# Check file type
$ file <filename>

# Check if executable
$ test -x <filename> && echo "Executable" || echo "Not executable"

# View executable sections
$ readelf -S <executable>

# View symbols
$ nm <binary>

# View dependencies
$ ldd <executable>

# Disassemble
$ objdump -d <binary>

# View hex dump
$ xxd <binary> | less
```

### **Windows (PowerShell):**

```powershell
# Check file type
> Get-Command .\program.exe

# View PE structure
> dumpbin /headers program.exe

# View dependencies
> dumpbin /dependents program.exe
```

### **macOS:**

```bash
# Check file type
$ file <filename>

# View Mach-O structure
$ otool -h <binary>

# View dependencies
$ otool -L <executable>
```

---

## **Language-Specific Artifacts**

### **C/C++:**

| File Type | Extension | Description |
|-----------|-----------|-------------|
| Source | `.c`, `.cpp`, `.cc` | Text |
| Header | `.h`, `.hpp` | Text |
| Object | `.o` (Unix), `.obj` (Win) | Binary, not executable |
| Static lib | `.a` (Unix), `.lib` (Win) | Binary, archive of objects |
| Shared lib | `.so` (Unix), `.dll` (Win) | Binary, dynamically loaded |
| Executable | (no ext Unix), `.exe` (Win) | Binary, runnable |

---

### **Rust:**

| File Type | Extension | Description |
|-----------|-----------|-------------|
| Source | `.rs` | Text |
| LLVM IR | `.ll` | Text (intermediate) |
| Assembly | `.s` | Text |
| Object | `.o` | Binary |
| Static lib | `.rlib` | Binary (Rust-specific) |
| Shared lib | `.so`/`.dll`/`.dylib` | Binary |
| Executable | (no ext Unix), `.exe` (Win) | Binary, runnable |

---

### **Go:**

| File Type | Extension | Description |
|-----------|-----------|-------------|
| Source | `.go` | Text |
| Object | `.o` (hidden in build cache) | Binary |
| Archive | `.a` (hidden in build cache) | Binary |
| Executable | (no ext Unix), `.exe` (Win) | Binary, runnable (statically linked!) |

**Go's Special Property:** Executables are **fully statically linked** by default (no external dependencies).

```bash
$ go build hello.go
$ ldd hello
    not a dynamic executable  # Self-contained!
```

---

### **Python (Interpreted, But Has Binaries):**

| File Type | Extension | Description |
|-----------|-----------|-------------|
| Source | `.py` | Text |
| Bytecode | `.pyc` | Binary (not directly executable) |
| Wheel | `.whl` | Binary distribution (zip archive) |
| Executable | N/A | Python interpreter itself is a binary |

---

## **Advanced Concept: Position-Independent Code (PIC)**

Modern executables often use **PIE (Position Independent Executable)**:

```bash
$ gcc -fPIE -pie hello.c -o hello_pie
$ file hello_pie
hello_pie: ELF 64-bit LSB pie executable, x86-64
```

**Why?**
- **Security:** ASLR (Address Space Layout Randomization) prevents exploits
- **Shared libs:** Can load at any memory address

---

## **The Mental Model: Abstraction Layers**

```
Level 5: Source Code (hello.c)         ← You write this
           ↓ [Preprocessing]
Level 4: Preprocessed Code (hello.i)   ← Macros expanded
           ↓ [Compilation]
Level 3: Assembly Code (hello.s)       ← Human-readable instructions
           ↓ [Assembly]
Level 2: Object Code (hello.o)         ← Machine code, unlinked
           ↓ [Linking]
Level 1: Executable (hello)            ← OS can run this
           ↓ [OS Loader]
Level 0: Process in Memory             ← Running program
```

---

## **Common Misconceptions**

### ❌ **"All binaries are executables"**
- **Wrong:** Images, videos, databases are binaries but not runnable.

### ❌ **"Scripts are executables"**
- **Nuanced:** A Python script (`.py`) is text, but with shebang (`#!/usr/bin/env python3`) + execute permission, the OS runs the **interpreter** (which IS an executable).

```bash
$ cat script.py
#!/usr/bin/env python3
print("Hello")

$ chmod +x script.py
$ ./script.py  # OS runs /usr/bin/python3 with script.py as argument
```

### ❌ **"Compiled = Binary"**
- **Nuanced:** Compilation often produces binary, but intermediate steps (LLVM IR, assembly) are text.

---

## **Elite-Level Insight: The ELF Magic Number**

Every ELF executable starts with:

```
7f 45 4c 46  (0x7f, 'E', 'L', 'F')
```

**Experiment:**

```bash
$ xxd /bin/ls | head -1
00000000: 7f45 4c46 0201 0100 0000 0000 0000 0000  .ELF............

$ echo -n -e '\x7fELF' | xxd
00000000: 7f45 4c46                                .ELF
```

The OS **reads these first 4 bytes** to determine file type. This is why you can't run arbitrary binaries—the OS checks the magic number!

---

## **Practical Exercise: Build Your Own Pipeline**

```bash
# C example
$ echo 'int main() { return 42; }' > test.c
$ gcc -E test.c > test.i      # Preprocess
$ gcc -S test.c               # Compile to assembly
$ gcc -c test.c               # Assemble to object
$ gcc test.c -o test          # Link to executable
$ ./test; echo $?             # Run and check exit code
42

# Rust example
$ echo 'fn main() { std::process::exit(42); }' > test.rs
$ rustc --emit=llvm-ir test.rs
$ rustc --emit=asm test.rs
$ rustc --emit=obj test.rs
$ rustc test.rs
$ ./test; echo $?
42
```

---

## **Summary: The Definitive Distinction**

**Binary:**
- General term for **non-text files**
- Includes executables, libraries, images, etc.
- **Cannot necessarily run**

**Executable:**
- **Specific type of binary**
- Contains **machine code + entry point**
- OS can **load and run** as a process
- Must conform to OS format (ELF/PE/Mach-O)

**Mnemonic:**
> "All executables are binaries, but not all binaries are executables—just like all squares are rectangles, but not all rectangles are squares."

---

## **Next-Level Questions for Deeper Mastery**

1. **Why can't you run a Windows .exe on Linux directly?**  
   *(Hint: Different executable formats—ELF vs. PE)*

2. **What's the difference between static and dynamic linking?**  
   *(This determines whether libraries are embedded or loaded at runtime)*

3. **How does the OS know where to start executing your program?**  
   *(Entry point address in the executable header)*

4. **Why are Go binaries so large compared to C?**  
   *(Static linking vs. dynamic linking)*

When you're ready, we'll explore these. For now, you've gained a **systems-level understanding** that 99% of programmers lack. This knowledge will serve you forever. 🔥