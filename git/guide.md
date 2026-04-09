# The Complete Git & Version Control Guide
## From First Principles to Production-Grade Workflows

> **Audience:** Developers at all levels who want a deep, accurate mental model of Git — not just commands, but *why* Git works the way it does.
> **Environment:** Linux/Ubuntu · VSCode · GitHub (concepts apply to any remote)
> **Philosophy:** Understand the data model first; the commands follow naturally.

---

## Table of Contents

1. [What Is Version Control — And Why Git?](#1-what-is-version-control--and-why-git)
2. [Git's Data Model — The Foundation](#2-gits-data-model--the-foundation)
3. [Installation, Identity, and Configuration](#3-installation-identity-and-configuration)
4. [The Three Trees — Working Directory, Index, HEAD](#4-the-three-trees--working-directory-index-head)
5. [Initializing and Cloning Repositories](#5-initializing-and-cloning-repositories)
6. [Staging and Committing](#6-staging-and-committing)
7. [Branches — Concept and Mechanics](#7-branches--concept-and-mechanics)
8. [Merging — All Strategies Explained](#8-merging--all-strategies-explained)
9. [Rebasing — In Depth](#9-rebasing--in-depth)
10. [Stashing — Concept and All Options](#10-stashing--concept-and-all-options)
11. [Remote Repositories — fetch, pull, push](#11-remote-repositories--fetch-pull-push)
12. [Tracking Branches and Upstream](#12-tracking-branches-and-upstream)
13. [Tags — Lightweight and Annotated](#13-tags--lightweight-and-annotated)
14. [Undoing Things — The Complete Taxonomy](#14-undoing-things--the-complete-taxonomy)
15. [git reset — Deep Dive](#15-git-reset--deep-dive)
16. [git revert — Safe Undo](#16-git-revert--safe-undo)
17. [git restore and git switch](#17-git-restore-and-git-switch)
18. [Cherry-Pick](#18-cherry-pick)
19. [git bisect — Bug Hunting](#19-git-bisect--bug-hunting)
20. [git blame and git log — Archaeology](#20-git-blame-and-git-log--archaeology)
21. [git reflog — Your Safety Net](#21-git-reflog--your-safety-net)
22. [Submodules](#22-submodules)
23. [Worktrees](#23-worktrees)
24. [Hooks — Automating at Git Events](#24-hooks--automating-at-git-events)
25. [gitignore, gitattributes, gitconfig](#25-gitignore-gitattributes-gitconfig)
26. [GitHub-Specific Concepts](#26-github-specific-concepts)
27. [Branching Strategies and Workflows](#27-branching-strategies-and-workflows)
28. [Commit Message Conventions](#28-commit-message-conventions)
29. [Conflict Resolution — In Depth](#29-conflict-resolution--in-depth)
30. [Security Considerations in Git](#30-security-considerations-in-git)
31. [Performance and Large Repositories](#31-performance-and-large-repositories)
32. [VSCode Git Integration](#32-vscode-git-integration)
33. [Common Mistakes and How to Fix Them](#33-common-mistakes-and-how-to-fix-them)
34. [Quick Reference Cheatsheet](#34-quick-reference-cheatsheet)

---

## 1. What Is Version Control — And Why Git?

### The Problem Version Control Solves

Without version control, developers copy folders (`project_v1`, `project_final`, `project_FINAL2`), lose history, cannot collaborate without overwriting each other's work, and cannot answer "what changed and why?".

A **Version Control System (VCS)** records changes to a set of files over time so you can:

- Recall specific versions later
- See who changed what and when
- Collaborate without conflict (or resolve conflicts explicitly)
- Experiment safely — roll back if something breaks

### Centralized vs Distributed VCS

| Property | Centralized (SVN, CVS) | Distributed (Git, Mercurial) |
|---|---|---|
| Repository location | Single server | Every clone is a full repo |
| Offline work | Limited | Full history available offline |
| Single point of failure | Yes | No |
| Speed | Network-dependent | Mostly local I/O |
| Branching cost | Expensive (file copies) | Cheap (40-byte pointer) |

### Why Git Won

Git was written by Linus Torvalds in 2005 for Linux kernel development. Its design goals:

- Speed at scale (thousands of contributors, millions of files)
- Data integrity (every object is content-addressed with SHA-1/SHA-256)
- Strong support for non-linear development (branching/merging as first-class citizens)
- Fully distributed — no single point of trust or failure

### Git vs GitHub — Critical Distinction

This is the single most common misconception:

- **Git** is a command-line tool and protocol. Free, open-source software installed on your machine. Works entirely offline.
- **GitHub** is a web-based hosting platform that hosts Git repositories and adds collaboration features: pull requests, issues, actions, wikis, etc.
- **Alternatives to GitHub:** GitLab (self-hostable), Bitbucket, Gitea, Forgejo, AWS CodeCommit, Azure DevOps, Sourcehut

You can use Git without GitHub. You can use GitHub without deeply understanding Git (but you will eventually hit walls).

---

## 2. Git's Data Model — The Foundation

Understanding Git's internals makes every command obvious and predictable. Git is fundamentally a **content-addressed key-value store** — a persistent map of hashes to objects — wrapped in a version control interface.

### The Object Store

Every piece of data in Git is an **object**, stored under `.git/objects/`. Each object is identified by the SHA-1 hash of its content (40 hex characters). Git is transitioning to SHA-256 for new repos (`git init --object-format=sha256`).

```
.git/
  objects/
    ab/
      cdef1234567890...  ← first 2 chars = directory, rest = filename
    pack/                ← packed objects for efficiency
    info/
```

### The Four Object Types

#### 1. Blob (Binary Large Object)

A blob stores the **raw content of a file** — just the bytes, nothing else. No filename, no permissions, no metadata. The filename is stored in the tree that references this blob.

```bash
# Hash a file without storing it
echo "hello world" | git hash-object --stdin
# 8c7e5a667f1b771847fe88c01c3de34413a1b220

# Hash and store a blob
echo "hello world" | git hash-object -w --stdin

# Read a blob by its hash
git cat-file -p 8c7e5a667f1b771847fe88c01c3de34413a1b220
# hello world

# Check object type
git cat-file -t 8c7e5a667f1b771847fe88c01c3de34413a1b220
# blob
```

**Key insight:** Two files with identical content share ONE blob object. Git deduplicates storage automatically.

#### 2. Tree

A tree represents a **directory listing**. It maps filenames and permissions to blob hashes (files) or other tree hashes (subdirectories).

```bash
# View the root tree of the current commit
git cat-file -p HEAD^{tree}
# 100644 blob a1b2c3d...  README.md
# 100644 blob d4e5f67...  main.go
# 040000 tree 789abcd...  pkg/

# View a subtree
git cat-file -p 789abcd
# 100644 blob aaabbb...  auth.go
# 100644 blob cccddd...  server.go
```

File mode values in trees:

| Mode | Meaning |
|---|---|
| `100644` | Regular file |
| `100755` | Executable file |
| `120000` | Symbolic link (blob content is link target) |
| `040000` | Directory (subtree reference) |
| `160000` | Gitlink (submodule reference) |

#### 3. Commit

A commit object stores:

- Pointer to the root **tree** (full snapshot of the project at this point)
- Pointers to **parent commit(s)** — zero for initial commit, two or more for merges
- **Author:** who wrote the change (name, email, timestamp)
- **Committer:** who recorded the commit (different when rebasing, cherry-picking, amending)
- The **commit message**

```bash
git cat-file -p HEAD
# tree 4b825dc642cb6eb9a060e54bf8d69288fbee4904
# parent a1b2c3d4e5f6789012345678901234567890abcd
# author Jane Doe <jane@example.com> 1700000000 +0000
# committer Jane Doe <jane@example.com> 1700000000 +0000
#
# feat: add authentication middleware
#
# Implements JWT validation with RSA-256 key pairs.
# Closes #42
```

**Critical insight:** A commit is a **snapshot**, not a diff. Git stores the complete state of every file at every commit. Git computes diffs on the fly by comparing trees. This is why `git diff HEAD~50 HEAD` is fast — it reads two tree objects and compares blobs, rather than replaying 50 diffs.

Because every field in a commit (tree, parents, author, message) feeds into its hash, **changing anything creates a completely new commit with a new hash**. This is why rebasing "rewrites history" — it creates new commit objects even if the content is identical.

#### 4. Tag (Annotated)

An annotated tag is a full Git object that points to another object (usually a commit) with tagger info, date, and a message. It is itself immutable and has a hash.

```bash
git cat-file -p v1.0.0
# object abc123def456...
# type commit
# tag v1.0.0
# tagger Jane Doe <jane@example.com> 1700000000 +0000
#
# Release version 1.0.0
# First stable production release.
```

Lightweight tags are just references (pointers to commits) — they are NOT objects.

### How Objects Link Together

```
Annotated Tag: v1.0.0
  └─► Commit: abc123
        ├── tree: def456   (root directory snapshot)
        │     ├── blob: aaa  README.md content
        │     ├── blob: bbb  main.go content
        │     └── tree: ccc  pkg/ directory
        │           └── blob: ddd  pkg/auth.go content
        └── parent: commit xyz789
              └── tree: ...  (previous snapshot)
```

All blobs and trees from the parent commit that are unchanged are **reused by hash**. A commit that changes one file out of 1000 only needs one new blob, a few new tree objects up the path, and the new commit object. The other 999 blobs are shared.

### References (Refs)

SHA hashes are unwieldy. Git uses **references** — named pointers to hashes.

```
.git/
  HEAD             ← points to current branch or commit directly
  refs/
    heads/         ← local branches
      main         ← file contains: abc123def456...
      feature-x    ← file contains: 789abc...
    remotes/       ← remote-tracking branches
      origin/
        main       ← last known state of origin/main
        develop    ← last known state of origin/develop
    tags/
      v1.0.0       ← lightweight tag (points to commit hash)
```

```bash
# What does HEAD point to?
cat .git/HEAD
# ref: refs/heads/main

# What commit is main at?
cat .git/refs/heads/main
# abc123def456789...

# Resolve any ref to a hash
git rev-parse HEAD
git rev-parse main
git rev-parse origin/main
git rev-parse v1.0.0^{}   # dereference tag to commit
```

### Commit References and Ancestry Syntax

```bash
HEAD        # current commit
HEAD~1      # first parent of HEAD (one commit back)
HEAD~3      # three commits back (following first parents)
HEAD^       # same as HEAD~1
HEAD^2      # second parent of HEAD (only meaningful for merge commits)
HEAD^^      # grandparent (HEAD~2)
abc123~2    # two commits before abc123
@{upstream} # the upstream tracking branch
@{-1}       # the previously checked-out branch
```

---

## 3. Installation, Identity, and Configuration

### Installation on Ubuntu

```bash
# Ubuntu default packages (may be older version)
sudo apt update && sudo apt install git

# Latest stable via official PPA
sudo add-apt-repository ppa:git-core/ppa
sudo apt update && sudo apt install git

# Verify
git --version
git --version  # should be 2.43+ as of 2024
```

### Identity — Mandatory First Step

Git attaches author/committer information to every commit. This is **metadata, not authentication** — anyone can set any name/email. Authentication is handled by SSH keys, tokens, or credentials separately.

```bash
# Global identity (stored in ~/.gitconfig — applies to all repos)
git config --global user.name "Your Full Name"
git config --global user.email "you@example.com"

# Local override (stored in .git/config — overrides global for this repo)
cd /path/to/work-project
git config user.name "Your Work Name"
git config user.email "you@company.com"
```

### Configuration Scopes and Precedence

Git has four config scopes, later ones override earlier ones:

| Scope | File | Flag | Applies To |
|---|---|---|---|
| System | `/etc/gitconfig` | `--system` | All users on this machine |
| Global | `~/.gitconfig` | `--global` | Your user account, all repos |
| Local | `.git/config` | `--local` | This repository only |
| Worktree | `.git/config.worktree` | `--worktree` | This worktree only |

```bash
# View all config with which file it came from
git config --list --show-origin --show-scope

# Get a specific value
git config user.email

# Set a value
git config --global core.editor "code --wait"

# Unset a value
git config --global --unset pull.rebase

# Edit the global config file directly
git config --global --edit
```

### Comprehensive Recommended Configuration

```bash
# ─── Core ───────────────────────────────────────────────
git config --global core.editor "code --wait"
git config --global core.autocrlf input        # Linux: convert CRLF→LF on commit
git config --global core.whitespace fix        # detect/fix whitespace errors
git config --global core.excludesfile ~/.gitignore_global

# ─── Branch defaults ────────────────────────────────────
git config --global init.defaultBranch main

# ─── Pull behavior ──────────────────────────────────────
# 'rebase' keeps linear history; 'merge' is the legacy default
git config --global pull.rebase true

# ─── Fetch ──────────────────────────────────────────────
git config --global fetch.prune true           # auto-delete stale remote refs

# ─── Push ───────────────────────────────────────────────
git config --global push.default current       # push current branch to same-named remote branch
git config --global push.autoSetupRemote true  # auto-set upstream on first push (Git 2.37+)

# ─── Diff and Merge ─────────────────────────────────────
git config --global diff.algorithm histogram   # better diff (more readable than Myers)
git config --global merge.conflictstyle diff3  # show base + ours + theirs in conflicts

# ─── Rerere (Reuse Recorded Resolution) ─────────────────
# Automatically reuse conflict resolutions you've already made
git config --global rerere.enabled true

# ─── Aliases ────────────────────────────────────────────
git config --global alias.st "status -sb"
git config --global alias.lg "log --oneline --graph --decorate --all"
git config --global alias.lp "log --pretty=format:'%C(yellow)%h%Creset %C(blue)%an%Creset %s %C(green)(%cr)%Creset'"
git config --global alias.unstage "restore --staged"
git config --global alias.undo "reset --soft HEAD~1"
git config --global alias.fpush "push --force-with-lease"
git config --global alias.aliases "config --get-regexp alias"
git config --global alias.contributors "shortlog -sn --no-merges"
```

Sample `~/.gitconfig` after all the above:

```ini
[user]
    name = Jane Doe
    email = jane@example.com

[core]
    editor = code --wait
    autocrlf = input
    whitespace = fix
    excludesfile = /home/jane/.gitignore_global

[init]
    defaultBranch = main

[pull]
    rebase = true

[fetch]
    prune = true

[push]
    default = current
    autoSetupRemote = true

[diff]
    algorithm = histogram

[merge]
    conflictstyle = diff3

[rerere]
    enabled = true

[alias]
    st = status -sb
    lg = log --oneline --graph --decorate --all
    lp = log --pretty=format:'%C(yellow)%h%Creset %C(blue)%an%Creset %s %C(green)(%cr)%Creset'
    unstage = restore --staged
    undo = reset --soft HEAD~1
    fpush = push --force-with-lease
    aliases = config --get-regexp alias
    contributors = shortlog -sn --no-merges
```

---

## 4. The Three Trees — Working Directory, Index, HEAD

This is the most critical mental model for understanding Git. Almost every Git mistake stems from not having this clear. Git manages three distinct named states of your files:

```
WORKING DIRECTORY       INDEX (Staging Area)        HEAD
  (your filesystem)       (.git/index)           (last commit)

  edit files         git add          git commit
 ─────────────► ─────────────────► ──────────────►
                git restore                git reset HEAD
              ◄─────────────── ◄──────────────────
                   git restore --staged
                ◄──────────────────────────────────
                         git reset --hard
```

### Working Directory

The actual files on your filesystem in the project directory. This is where you edit. Files are one of:

- **Unmodified tracked:** In last commit, not changed locally
- **Modified tracked:** In last commit, changed locally (not yet staged)
- **Staged:** Changes added to index, will be in next commit
- **Untracked:** New file, Git has never seen it
- **Ignored:** Matches a `.gitignore` pattern

### The Index (Staging Area / Cache)

The index is a binary file at `.git/index`. Think of it as a **"proposed next commit"** that you build up file-by-file (or hunk-by-hunk). It starts as a copy of HEAD and you modify it with `git add`.

This two-phase workflow (edit → stage → commit) is deliberate:
- You can make 10 changes but commit only 3, making history cleaner
- You can review exactly what will be committed before committing
- You can split a large change into logical commits

```bash
# What does the index currently contain?
git ls-files --stage
# 100644 sha1hash 0  filename.go

# What changed between index and HEAD? (what you've staged)
git diff --staged
git diff --cached    # same thing

# What changed between working dir and index? (what you've NOT staged)
git diff

# What changed between working dir and HEAD? (everything)
git diff HEAD
```

### HEAD

HEAD points to the current commit — the snapshot that your working directory was populated from and the parent of your next commit.

```bash
# What commit is HEAD?
git log -1 --oneline

# Where does HEAD point?
cat .git/HEAD
# ref: refs/heads/main     ← attached HEAD (normal)
# abc123def456...          ← detached HEAD

# Detached HEAD state
git checkout abc123   # HEAD now points directly to a commit, not a branch
# WARNING: you are in 'detached HEAD' state
# Any commits you make are not reachable from any branch name
# They will be garbage-collected unless you create a branch
git switch -c new-branch  # rescue by creating a branch here
```

---

## 5. Initializing and Cloning Repositories

### git init

Creates a new, empty repository in the current directory.

```bash
mkdir my-project && cd my-project
git init
# Initialized empty Git repository in /home/user/my-project/.git/

# Specify branch name explicitly (override global default)
git init -b main

# Create a bare repository (used for hosting/remote — no working directory)
git init --bare /srv/repos/project.git
```

A **bare repository** contains only the `.git` contents, with no working directory. This is the format used by GitHub, GitLab, and any Git server. You push to bare repos; you work in non-bare clones.

### git clone

Downloads an existing repository fully — all objects, all history, all branches:

```bash
# Clone via HTTPS
git clone https://github.com/org/repo.git

# Clone via SSH (requires SSH key pair configured on GitHub/GitLab)
git clone git@github.com:org/repo.git

# Clone into a specific local directory name
git clone git@github.com:org/repo.git my-local-name

# Shallow clone — only the most recent N commits (faster, less data)
# WARNING: limited git operations available; reflog/bisect affected
git clone --depth=1 git@github.com:org/repo.git

# Unshallow a shallow clone later
git fetch --unshallow

# Clone a single branch only
git clone --branch develop --single-branch git@github.com:org/repo.git

# Mirror clone — all refs, bare, for backup/migration
git clone --mirror git@github.com:org/repo.git repo.git
```

### Protocols Explained

| Protocol | URL Format | Auth | Use Case |
|---|---|---|---|
| HTTPS | `https://github.com/org/repo.git` | Token/password | Simple, works everywhere |
| SSH | `git@github.com:org/repo.git` | SSH key pair | Preferred for daily dev |
| Git | `git://host/repo.git` | None | Read-only, fast (rare now) |
| Local | `/path/to/repo.git` | Filesystem | Testing, local mirrors |

### Adding and Managing Remotes

`origin` is just the conventional name for the remote you cloned from. You can have many:

```bash
git remote -v                              # list all remotes
git remote add upstream git@github.com:org/original-repo.git
git remote add fork git@github.com:you/repo.git
git remote rename origin old-origin
git remote remove old-origin
git remote set-url origin git@github.com:org/repo.git  # change URL
```

---

## 6. Staging and Committing

### Checking Repository Status

```bash
git status           # full descriptive output
git status -s        # short format
git status -sb       # short + branch tracking info (recommended)
```

Short format key:
```
?? untracked-file.go       ← never staged, not tracked
A  new-staged-file.go      ← new file staged for commit
M  modified-staged.go      ← staged modification
 M modified-unstaged.go    ← modified but NOT staged (space before M)
MM both-staged-unstaged.go ← has staged AND additional unstaged changes
D  staged-delete.go        ← deletion staged
 D unstaged-delete.go      ← deletion not staged
R  old.go -> new.go        ← rename staged
```

### git add — Building the Index

```bash
# Stage a specific file
git add main.go

# Stage multiple files
git add main.go handler.go

# Stage all changes in a directory
git add src/

# Stage everything (new, modified, deleted) from repo root
git add -A
git add --all

# Stage only modifications to already-tracked files (no new untracked)
git add -u
git add --update

# Stage interactively — choose hunks (LEARN THIS — very powerful)
git add -p
git add --patch
```

### git add --patch (Interactive Hunk Staging)

This is one of Git's most powerful features. It shows each changed hunk and asks what to do:

```
@@ -10,7 +10,9 @@ func main() {
     fmt.Println("starting server")
+    log.SetOutput(os.Stderr)
+    log.SetFlags(log.LstdFlags | log.Lshortfile)
     server := NewServer()

Stage this hunk [y,n,q,a,d,s,e,?]?
```

Options:
- `y` — stage this hunk
- `n` — skip this hunk (don't stage)
- `q` — quit, don't stage any more hunks
- `a` — stage this and all remaining hunks in this file
- `d` — don't stage this or any remaining hunks in this file
- `s` — split hunk into smaller hunks (if possible)
- `e` — manually edit the hunk in your editor
- `?` — show help

This lets you make 5 logical changes to a file and commit them as 5 separate commits, keeping history clean.

### git commit — Recording Changes

```bash
# Commit staged changes, open editor for message
git commit

# Commit with inline message
git commit -m "feat: add user authentication"

# Stage all tracked changes AND commit (skips git add for tracked files)
git commit -a -m "fix: correct off-by-one error"
# WARNING: -a does NOT stage new untracked files

# Amend the last commit (changes message and/or staged content)
# DO NOT amend commits already pushed to a shared branch
git commit --amend
git commit --amend -m "corrected commit message"
git commit --amend --no-edit   # keep same message, just update content

# Commit with a future/past date
git commit --date="2024-01-15T10:00:00" -m "backdated commit"

# Create an empty commit (useful for triggering CI)
git commit --allow-empty -m "chore: trigger CI pipeline"
```

### Viewing What You're About to Commit

Always a good habit:

```bash
git diff --staged          # see exactly what will be committed
git status -sb             # see which files are staged
git log --oneline -5       # see recent history for context
```

---

## 7. Branches — Concept and Mechanics

### What Is a Branch, Really?

A branch is **just a file containing a 40-character SHA-1 hash**, stored in `.git/refs/heads/`. That's it.

```bash
cat .git/refs/heads/main
# abc123def456789012345678901234567890abcd
```

When you make a new commit on branch `main`, Git:
1. Creates the new commit object with HEAD as parent
2. Updates `.git/refs/heads/main` to the new commit's hash

That's all branching is — a movable pointer. Creating a branch is O(1): write 40 bytes to a file. This is why Git branching is "free" compared to SVN where branching copied entire directories.

### Creating, Switching, and Deleting Branches

```bash
# Create a branch (does NOT switch to it)
git branch feature-auth

# Create and switch in one step (modern syntax)
git switch -c feature-auth
# Old syntax (still works)
git checkout -b feature-auth

# Create branch at a specific commit
git branch bugfix-123 abc123def456
git switch -c hotfix v1.2.3      # branch from a tag

# Switch to an existing branch
git switch main
git checkout main                 # old syntax

# List branches
git branch                       # local branches
git branch -r                    # remote-tracking branches
git branch -a                    # all (local + remote-tracking)
git branch -v                    # with last commit info
git branch -vv                   # with upstream tracking info

# Delete a branch (safe — refuses if unmerged)
git branch -d feature-auth

# Force delete (even if unmerged — data loss possible)
git branch -D feature-auth

# Rename a branch
git branch -m old-name new-name
git branch -m new-name           # rename current branch

# Delete a remote branch
git push origin --delete feature-auth
git push origin :feature-auth    # older syntax (same effect)
```

### HEAD and Branch Relationship

```
main ──► commit C ──► commit B ──► commit A
  ▲
HEAD (attached — you're on main)

After git switch feature:

main ──► commit C ──► commit B ──► commit A
                          ▲
feature ──────────────────┘
  ▲
HEAD (attached — you're on feature)

After a commit on feature:

main ──► commit C ──► commit B ──► commit A
                          ▲
             commit D ────┘
               ▲
feature ───────┘
  ▲
HEAD
```

### Detached HEAD

Detached HEAD means HEAD points directly to a commit hash, not to a branch name. Any commits made will be "floating" — not reachable by any branch name and eligible for garbage collection.

```bash
# Causes detached HEAD
git checkout abc123        # specific commit
git checkout v1.0.0        # tag (lightweight)
git checkout origin/main   # remote-tracking branch

# Check if detached
git status                 # will say "HEAD detached at..."

# Rescue work done in detached HEAD
git switch -c rescue-branch    # create branch at current commit

# Or discard and go back
git switch main
```

---

## 8. Merging — All Strategies Explained

Merging integrates changes from one branch into another. Git offers several merge strategies.

### Fast-Forward Merge

If the target branch is directly behind the source — i.e., no new commits were made on target since the branches diverged — Git can simply move the pointer forward. No merge commit is created.

```
Before:
main ──► A ──► B
                └──► C ──► D  (feature)

git switch main
git merge feature

After (fast-forward):
main ──► A ──► B ──► C ──► D
                             ▲
                           feature
```

```bash
git switch main
git merge feature         # fast-forward if possible

# Force a merge commit even when fast-forward is possible
git merge --no-ff feature

# Only allow fast-forward (fail if not possible)
git merge --ff-only feature
```

`--no-ff` (no fast-forward) is often preferred in team workflows because it preserves the "this group of commits was a feature branch" context in the graph.

### Three-Way Merge (True Merge)

When both branches have diverged (both have new commits since the common ancestor), Git performs a three-way merge using: the common ancestor (base), the current branch (ours), and the branch being merged (theirs).

```
Before:
main ──► A ──► B ──► E (main has new work)
                └──► C ──► D  (feature has its own work)

git switch main
git merge feature

After (merge commit M):
main ──► A ──► B ──► E ──► M (merge commit — has 2 parents: E and D)
                └──► C ──► D ─┘
```

```bash
git switch main
git merge feature
# Auto-merging file.go
# Merge made by the 'ort' strategy.

# Check merge commit
git log --oneline --graph --all
```

### Merge Strategies (--strategy flag)

```bash
git merge --strategy=ort feature        # default modern strategy (Git 2.33+)
git merge --strategy=recursive feature  # older default
git merge --strategy=octopus br1 br2    # merge multiple branches at once
git merge --strategy=ours feature       # discard all changes from theirs
git merge --strategy=subtree feature    # for subtree merges
```

### Merge Strategy Options (--strategy-option / -X)

```bash
# When conflict: prefer "ours" (current branch) automatically
git merge -X ours feature

# When conflict: prefer "theirs" automatically
git merge -X theirs feature

# Ignore whitespace differences
git merge -X ignore-all-space feature
```

### Squash Merge

Takes all commits from the source branch and squashes them into the index as a single staged change. You then commit once. This keeps main's history clean.

```bash
git switch main
git merge --squash feature
git commit -m "feat: implement authentication"
# The feature branch commits are NOT in main's history
# The feature branch is NOT merged (no merge commit)
# The feature branch still exists and must be deleted manually
git branch -d feature   # may need -D since no merge commit exists
```

Squash merge is popular for "clean main" policies (all commits on main are meaningful) but loses per-commit authorship and granularity.

### Aborting a Merge

```bash
# Mid-conflict, if you want to start over
git merge --abort

# Check current merge state
cat .git/MERGE_HEAD    # exists during a merge
```

---

## 9. Rebasing — In Depth

### What Rebasing Does

Rebasing **replays commits** from one branch on top of another. It produces **new commit objects** even if content is identical, because the parent hash changes.

```
Before:
main ──► A ──► B ──► E
                └──► C ──► D  (feature, branched from B)

git switch feature
git rebase main

After:
main ──► A ──► B ──► E
                      └──► C' ──► D'  (new commits, replayed on E)
                ▲
              feature
```

C' and D' are NEW commits with new hashes. C and D become unreachable and will be garbage-collected (but visible in reflog temporarily).

### Why Rebase?

- **Cleaner history:** Linear progression without merge commits cluttering the graph
- **Cleaner reviews:** Feature branch commits sit cleanly on top of main, easy to diff
- **No "merge noise":** `git log --oneline` reads like a story

### Basic Rebase

```bash
git switch feature-branch
git rebase main              # replay feature commits on top of current main
git rebase main feature-branch  # rebase feature onto main (without switching first)

# After rebase, update remote (requires force push — see caution below)
git push --force-with-lease origin feature-branch
```

### The Golden Rule of Rebasing

**NEVER rebase commits that exist on a public/shared branch.**

When you rebase, you create new commits and abandon the old ones. If someone else based work on the old commits, they now have orphaned history that no longer connects to your rebased branch. This creates a mess that is painful to untangle.

- ✅ Safe to rebase: your local feature branch before merging
- ✅ Safe to rebase: a branch only you are using
- ❌ Never rebase: `main`, `develop`, any shared branch
- ❌ Never rebase: commits that others have pulled

### Interactive Rebase — The Most Powerful Git Feature

Interactive rebase lets you **edit, reorder, squash, drop, or reword** any commits in your history before sharing.

```bash
# Interactively rebase the last 5 commits
git rebase -i HEAD~5

# Interactively rebase everything since branching from main
git rebase -i main

# Interactively rebase from a specific commit
git rebase -i abc123^   # the ^ means "start from commit before abc123"
```

The editor opens with something like:

```
pick a1b2c3 feat: add user model
pick d4e5f6 fix typo
pick 789abc wip: half-finished middleware
pick 012def feat: add login endpoint
pick 345678 fix: actually finish middleware

# Rebase from a1b2c3..345678 onto parent (5 commands)
#
# Commands:
# p, pick   = use commit as-is
# r, reword = use commit, but edit the commit message
# e, edit   = use commit, but stop for amending (add/change files)
# s, squash = melt into previous commit, combine messages
# f, fixup  = melt into previous commit, discard this message
# x, exec   = run shell command
# b, break  = stop here (continue with git rebase --continue)
# d, drop   = remove this commit entirely
# l, label  = label current HEAD with a name
# t, reset  = reset HEAD to a label
# m, merge  = create a merge commit
```

Example: clean up before opening a PR:

```
reword a1b2c3 feat: add user model
fixup  d4e5f6 fix typo              ← merge typo fix into previous
drop   789abc wip: half-finished    ← delete this commit entirely
reword 012def feat: add login endpoint
squash 345678 fix: finish middleware ← combine with previous, edit message
```

After saving and closing the editor, Git processes each step, opening editors for `reword` and `squash` messages.

### Fixing Conflicts During Rebase

When replaying a commit causes a conflict:

```bash
# 1. Fix the conflict in the file
# 2. Stage the resolution
git add conflicted-file.go

# 3. Continue the rebase
git rebase --continue

# OR: skip this commit entirely (unusual)
git rebase --skip

# OR: abort and go back to pre-rebase state
git rebase --abort
```

### git pull --rebase

Instead of creating a merge commit when pulling, rebases your local commits on top of the fetched commits:

```bash
git pull --rebase
# equivalent to:
git fetch origin
git rebase origin/main

# Set as default (recommended)
git config --global pull.rebase true
```

### Rebase vs Merge — When to Use Which

| Scenario | Recommendation |
|---|---|
| Feature branch before PR/merge | Rebase onto main for clean history |
| Integrating main into long-running feature | Either; rebase gives cleaner result |
| Merging feature into main | Merge (with --no-ff) to preserve branch structure |
| Shared public branches | NEVER rebase |
| Fixing up local commits before push | Interactive rebase |
| Hotfix that needs to go to multiple branches | Cherry-pick |

---

## 10. Stashing — Concept and All Options

### The Problem Stash Solves

You're working on a feature. An urgent bug is reported. You need to switch branches, but your working directory has uncommitted changes you don't want to commit yet. `git stash` saves them temporarily.

### What Stash Actually Is

A stash is stored as a special commit object in `refs/stash` (the stash stack). Each stash is a commit with two or three parents:
- Parent 1: the commit HEAD pointed to when you stashed
- Parent 2: the index (staged changes)
- Parent 3: untracked files (only with `-u`)

This means stashes are just commits — they can't be lost (until you drop them), they have full content, and they work across branches.

### Basic Stash Operations

```bash
# Stash all staged and unstaged changes to tracked files
git stash
git stash push          # same as above (explicit)

# Stash with a descriptive message (HIGHLY RECOMMENDED)
git stash push -m "WIP: refactoring auth middleware"

# Include untracked files (new files not yet git add-ed)
git stash push -u
git stash push --include-untracked

# Include untracked AND ignored files
git stash push -a
git stash push --all

# Stash specific files only
git stash push -m "just the handler" -- handler.go routes.go

# Stash using patch mode (interactively choose hunks)
git stash push -p
```

### Viewing the Stash Stack

```bash
# List all stashes
git stash list
# stash@{0}: WIP on feature-x: abc123 last commit message
# stash@{1}: On main: WIP: refactoring auth middleware
# stash@{2}: WIP on bugfix-99: def456 fix null pointer

# Show what a stash contains (diff)
git stash show                   # shows stash@{0} stat
git stash show -p                # shows stash@{0} full diff
git stash show stash@{2}         # shows specific stash stat
git stash show -p stash@{1}      # shows specific stash full diff
```

### Applying Stashes

```bash
# Apply the most recent stash AND remove it from stash list (most common)
git stash pop

# Apply the most recent stash but KEEP it in the stash list
git stash apply

# Apply a specific stash
git stash pop stash@{2}
git stash apply stash@{1}

# Apply stash to a new branch (useful when context has changed)
git stash branch new-branch-name stash@{0}
# This creates a new branch, checks it out, applies the stash,
# and drops it from the stash list if successful
```

### Managing Stashes

```bash
# Delete the most recent stash
git stash drop
git stash drop stash@{2}  # delete specific stash

# Delete ALL stashes
git stash clear           # WARNING: irreversible (though reflog may help)
```

### Stash Conflicts

If applying a stash conflicts with your current working tree, Git marks conflicts just like a merge. Resolve them, then:

```bash
# After resolving stash conflicts
git add resolved-file.go
# No --continue needed for stash; the stash has been applied (partially)
# If you used pop, the stash is already removed
# If conflicts remain, fix them manually
```

### The Stash Stack is LIFO

Stash is a **stack** (Last In, First Out):
- `git stash push` pushes to index 0 (top), shifting others up
- `git stash pop` pops from index 0 (top)

Always use descriptive messages (`-m`) to remember what each stash contains.

---

## 11. Remote Repositories — fetch, pull, push

### The Conceptual Model

```
Your machine                            Remote (GitHub)
─────────────────────────────────────   ─────────────────────
Working Directory                       origin/main  (server)
     │
   .git/
     ├── refs/heads/main    ←──── your local main
     └── refs/remotes/
           └── origin/
                 └── main   ←──── snapshot of remote (updated by fetch)
```

Remote-tracking branches (`origin/main`) are **read-only snapshots** of where the remote was last time you communicated with it. They are not automatically updated.

### git fetch — Download Without Integrating

```bash
# Fetch all branches from origin
git fetch origin

# Fetch specific branch
git fetch origin main

# Fetch ALL remotes
git fetch --all

# Fetch and prune deleted remote branches
git fetch --prune
git fetch -p

# Fetch tags too
git fetch --tags

# Fetch and see what changed
git fetch origin && git log HEAD..origin/main --oneline
```

`git fetch` NEVER modifies your local branches or working directory. It only updates `refs/remotes/`. It is always safe to run.

### git pull — Fetch + Integrate

`git pull` is a convenience command that does `git fetch` + either `git merge` or `git rebase`:

```bash
# Default: fetch + merge (or rebase if pull.rebase=true)
git pull

# Explicitly rebase (preferred for keeping linear history)
git pull --rebase

# Explicitly merge
git pull --no-rebase

# Pull from a specific remote and branch
git pull origin main

# Pull and use fast-forward only (fail if not possible)
git pull --ff-only
```

`git pull` can surprise you because it changes your working state. Prefer `git fetch` + manual integration for more control.

### git push — Upload Your Commits

```bash
# Push current branch to its configured upstream
git push

# Push to explicit remote and branch
git push origin main

# Push and set upstream tracking (first push of a new local branch)
git push -u origin feature-auth
git push --set-upstream origin feature-auth

# Push all local branches
git push --all origin

# Push all tags
git push --tags

# Delete a remote branch
git push origin --delete feature-old
git push origin :feature-old    # older syntax

# Push a tag
git push origin v1.0.0
git push origin --tags          # push all tags
```

### Force Push — Use With Extreme Caution

After a rebase or amend, your local branch history diverges from the remote. You need to force-push:

```bash
# DANGEROUS: overwrites remote history, others may lose work
git push --force

# SAFER: only pushes if remote tip hasn't changed since your last fetch
# Prevents overwriting someone else's push
git push --force-with-lease

# Even safer: specify what you expect the remote to be
git push --force-with-lease=main:abc123

# Alias (recommended)
git config --global alias.fpush "push --force-with-lease"
git fpush
```

Rules for force push:
- ✅ OK to force push to your own feature branches (only you use them)
- ✅ OK on PR branches before merging
- ❌ NEVER force push to `main`, `master`, `develop`, or any shared branch
- ❌ NEVER force push without warning collaborators

---

## 12. Tracking Branches and Upstream

### What Is a Tracking Branch?

A **tracking branch** (also called an upstream relationship) is a link between a local branch and a remote-tracking branch. Once set, Git knows:
- Where to push when you run `git push` (no argument)
- Where to fetch/pull from when you run `git pull` (no argument)
- How many commits ahead/behind you are (`git status -sb` shows this)

### Viewing Tracking Relationships

```bash
git branch -vv
# * main        abc123 [origin/main] last commit message
#   feature-x   def456 [origin/feature-x: ahead 3] local commits
#   local-only  789abc no upstream set

# Show remote configuration
git remote show origin
```

### Setting Upstream

```bash
# Set upstream when pushing (most common)
git push -u origin feature-auth
git push --set-upstream origin feature-auth

# Set upstream without pushing
git branch --set-upstream-to=origin/main main
git branch -u origin/feature-x feature-x

# Unset upstream
git branch --unset-upstream
```

### Ahead and Behind

```bash
git status -sb
# ## main...origin/main [ahead 2, behind 1]
# This means:
# - You have 2 commits not on remote
# - Remote has 1 commit you don't have (need to pull)

# See the actual commits ahead/behind
git log HEAD..origin/main --oneline   # commits on remote, not local
git log origin/main..HEAD --oneline   # commits local, not on remote
```

---

## 13. Tags — Lightweight and Annotated

Tags mark specific points in history (usually releases). Unlike branches, tags don't move.

### Lightweight Tags

A lightweight tag is just a named pointer to a commit (a file in `.git/refs/tags/`). No metadata.

```bash
git tag v1.0.0              # tag current HEAD
git tag v1.0.0 abc123       # tag a specific commit
```

### Annotated Tags

An annotated tag is a full Git object with tagger, date, message, and optionally a GPG signature. Use these for releases.

```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git tag -a v1.0.0 abc123 -m "Tagging the 1.0.0 release commit"

# Signed tag (requires GPG key configured)
git tag -s v1.0.0 -m "Signed release 1.0.0"

# View tag details
git show v1.0.0
git cat-file -p v1.0.0      # raw object
```

### Managing Tags

```bash
# List tags
git tag
git tag -l "v1.*"           # filter by pattern

# Push a tag to remote (tags are NOT pushed by default)
git push origin v1.0.0
git push origin --tags       # push all tags

# Delete local tag
git tag -d v1.0.0

# Delete remote tag
git push origin --delete v1.0.0
git push origin :refs/tags/v1.0.0   # older syntax

# Move a tag (requires delete + recreate + force push — avoid in production)
git tag -d v1.0.0
git tag -a v1.0.0 new-commit -m "moved tag"
git push origin --force refs/tags/v1.0.0
```

### Checking Out a Tag

```bash
git checkout v1.0.0         # detached HEAD — you can look but not commit cleanly
git switch -c release-1.0   # create a branch from tag to do work
```

---

## 14. Undoing Things — The Complete Taxonomy

This is where most developers get confused. There are many ways to "undo" in Git, each with different scope and permanence.

```
What you want to undo          →   Command
────────────────────────────────────────────────────────────────────
Staged changes (before commit) →   git restore --staged <file>
                                   git reset HEAD <file>  (older)

Unstaged changes (working dir) →   git restore <file>
                                   git checkout -- <file>  (older)

Last commit (keep changes)     →   git reset --soft HEAD~1
Last commit (unstage changes)  →   git reset --mixed HEAD~1  (default)
Last commit (discard changes)  →   git reset --hard HEAD~1

Old commit (public-safe)       →   git revert <commit>
Multiple old commits           →   git revert <oldest>..<newest>

Commit message (last commit)   →   git commit --amend
                                   (only before push)

Commit on wrong branch         →   git cherry-pick <commit>
                                   (then reset/drop original)

Deleted branch                 →   git branch <name> <hash-from-reflog>
Deleted file                   →   git checkout HEAD -- <file>
                                   git restore --source=HEAD <file>
```

---

## 15. git reset — Deep Dive

`git reset` moves the HEAD (and thus the branch pointer) to a specified commit, with different effects on the index and working directory depending on the mode.

### The Three Modes

```
                         HEAD pointer    Index        Working Dir
git reset --soft  SHA  │   moved     │ unchanged  │  unchanged  │
git reset --mixed SHA  │   moved     │  reset     │  unchanged  │  ← DEFAULT
git reset --hard  SHA  │   moved     │  reset     │   reset     │
```

### --soft: Move HEAD Only

The branch pointer moves back; your index and files are untouched. All the commits you "undid" are now staged.

```bash
# Undo last 3 commits, but keep all their changes staged
git reset --soft HEAD~3

# Use case: squash last N commits into one
git reset --soft HEAD~5
git commit -m "feat: complete user authentication system"
```

### --mixed: Move HEAD and Reset Index (Default)

The branch pointer moves back AND the index is reset to match the new HEAD. Your files are untouched, but changes from undone commits are now UNSTAGED (in working directory as modifications).

```bash
# Undo last commit, keep changes as unstaged modifications
git reset HEAD~1
git reset --mixed HEAD~1    # same

# Unstage a specific file (HEAD stays the same)
git reset HEAD main.go
# Equivalent: git restore --staged main.go (modern)
```

### --hard: Move HEAD, Reset Index, Reset Working Directory

The most drastic mode. Everything is reset to the target commit — index and working directory are both overwritten. **Uncommitted changes are lost.**

```bash
# Completely discard last commit AND all its changes
git reset --hard HEAD~1

# Reset everything to match origin/main (discard ALL local changes)
git reset --hard origin/main

# Reset to specific commit
git reset --hard abc123
```

**WARNING:** `--hard` discards uncommitted changes permanently. Committed changes can be recovered via `git reflog` if acted on quickly. Uncommitted changes (unstaged, untracked) are gone.

### Resetting Specific Paths

When you specify a path, `git reset` only affects the index (not HEAD or working dir):

```bash
# Unstage a specific file (move it from index back to modified)
git reset HEAD -- main.go
git reset -- main.go        # HEAD is implied

# Unstage to a specific version
git reset abc123 -- main.go    # index gets main.go from commit abc123
```

---

## 16. git revert — Safe Undo

`git revert` creates a NEW commit that undoes the changes of a previous commit. It does NOT rewrite history — it adds history. This is the safe way to undo on shared branches.

```bash
# Revert the most recent commit
git revert HEAD

# Revert a specific commit by hash
git revert abc123def456

# Revert a range of commits (oldest first)
git revert abc123..def456

# Revert without auto-committing (stage changes for you to review)
git revert --no-commit abc123
git revert -n abc123

# After --no-commit, you can edit/review then commit
git commit -m "revert: undo changes from feature-x"

# Revert a merge commit (must specify which parent to "continue from")
git revert -m 1 abc123    # keep parent 1 (main line), undo parent 2 (feature)
git revert -m 2 abc123    # keep parent 2 (feature), undo parent 1 (rare)
```

### Revert vs Reset

| Aspect | git revert | git reset |
|---|---|---|
| History | Adds new commit | Rewrites/removes commits |
| Safe for shared branches | YES | NO (except --soft/--mixed on local only) |
| Visible undo | Yes (revert commit visible) | History appears to never have had the commits |
| Undo the undo | Revert the revert commit | Pop from reflog |

---

## 17. git restore and git switch

Git 2.23 (2019) introduced `git restore` and `git switch` to separate concerns that were bundled into the confusing `git checkout` command.

### git restore — Restore Working Tree Files

```bash
# Discard unstaged changes to a file (restore from index)
git restore main.go
git checkout -- main.go      # old equivalent

# Discard all unstaged changes
git restore .

# Unstage a file (restore index from HEAD)
git restore --staged main.go
git reset HEAD main.go        # old equivalent

# Unstage ALL staged changes
git restore --staged .

# Restore a file from a specific commit
git restore --source=abc123 main.go
git restore --source=HEAD~3 main.go

# Restore both index and working tree from commit
git restore --source=HEAD --staged --worktree main.go

# Restore a deleted file
git restore --source=HEAD main.go   # brings it back from last commit
```

### git switch — Switch Branches

```bash
# Switch to an existing branch
git switch main
git checkout main             # old equivalent

# Create and switch to a new branch
git switch -c feature-auth
git checkout -b feature-auth  # old equivalent

# Create branch from specific start point
git switch -c hotfix v1.2.3
git switch -c feature origin/feature  # start from remote branch

# Return to previously checked-out branch
git switch -
git checkout -                # old equivalent

# Force switch (discard local changes — dangerous)
git switch --discard-changes feature
git switch -f feature
```

### git checkout — The Old Way (Still Valid)

`git checkout` still works and has additional capabilities:

```bash
git checkout main               # switch branch
git checkout -b feature         # create + switch
git checkout -- file.go         # discard file changes (old restore)
git checkout abc123             # detached HEAD at commit
git checkout abc123 -- file.go  # restore specific file from commit
```

---

## 18. Cherry-Pick

Cherry-pick applies the changes introduced by a specific commit onto your current branch. It creates a new commit (new hash, same change).

```bash
# Apply a specific commit from another branch
git cherry-pick abc123

# Apply multiple commits
git cherry-pick abc123 def456 789ghi

# Apply a range of commits (inclusive)
git cherry-pick abc123^..def456

# Cherry-pick without auto-committing (stage only)
git cherry-pick --no-commit abc123
git cherry-pick -n abc123

# Cherry-pick and preserve original author (not committer)
git cherry-pick -x abc123       # appends "(cherry picked from commit...)" to message

# Abort a cherry-pick in progress
git cherry-pick --abort

# Continue after resolving conflicts
git cherry-pick --continue
```

### When to Use Cherry-Pick

- Backporting a fix from `main` to a release branch
- Pulling a specific feature from a branch before the whole branch is ready
- Applying a commit from an abandoned branch

### Cherry-Pick vs Merge vs Rebase

| Use case | Tool |
|---|---|
| Apply one specific commit | cherry-pick |
| Apply all commits from a branch | merge or rebase |
| Apply commits in order, updating parent | rebase |
| Apply in reverse (undo) | revert |

---

## 19. git bisect — Bug Hunting

`git bisect` uses binary search to find the commit that introduced a bug. If you have 1000 commits and a test to verify good/bad, bisect finds the culprit in ~10 steps.

```bash
# Start bisect session
git bisect start

# Mark current commit as bad (has the bug)
git bisect bad
git bisect bad HEAD

# Mark a known-good commit
git bisect good v1.5.0
git bisect good abc123

# Git checks out the midpoint commit — test it, then:
git bisect good    # this commit is fine
git bisect bad     # this commit has the bug

# Git repeats until it finds the first bad commit
# Output: "abc123 is the first bad commit"

# See the bisect log
git bisect log

# Reset to original state when done
git bisect reset

# Automated bisect with a test script
# Script exits 0 for good, non-zero for bad
git bisect start
git bisect bad HEAD
git bisect good v1.5.0
git bisect run ./test-script.sh
# Git automatically runs the script on each midpoint
```

---

## 20. git blame and git log — Archaeology

### git blame

Shows who last modified each line of a file and in which commit:

```bash
# Blame a file
git blame main.go

# Output format:
# hash (Author Date Time Timezone LineNum) content
# abc123de (Jane Doe 2024-01-15 10:00:00 +0000  42) func NewServer() *Server {

# Blame with email
git blame -e main.go

# Blame a specific range of lines
git blame -L 10,25 main.go
git blame -L '/func NewServer/,+20' main.go   # regex range

# Blame and ignore whitespace changes
git blame -w main.go

# Blame and detect moved/copied lines
git blame -M main.go       # moved within file
git blame -C main.go       # moved from other files in same commit
git blame -CC main.go      # moved from other files in any commit

# Blame at a specific revision
git blame v1.0.0 -- main.go
git blame abc123 -- main.go
```

### git log — History Exploration

```bash
# Basic log
git log

# One-line summary
git log --oneline

# Graph view (essential for understanding branches)
git log --oneline --graph --decorate --all

# Limit to N commits
git log -5

# Log for a specific file
git log -- main.go
git log --follow -- main.go   # follow renames

# Log by author
git log --author="Jane Doe"
git log --author="jane@example.com"

# Log by date range
git log --since="2024-01-01"
git log --until="2024-06-30"
git log --since="2 weeks ago"

# Log by commit message
git log --grep="authentication"
git log --grep="fix" -i   # case-insensitive

# Log by content change (pickaxe — find when a string was added/removed)
git log -S "password_hash"         # string appears/disappears
git log -G "password.*hash"        # regex matches diff

# Log with diff
git log -p                         # full diff for each commit
git log -p -- main.go              # diff for specific file
git log --stat                     # file change summary
git log --name-only                # just filenames changed
git log --name-status              # filenames + A/M/D status

# Pretty formatting
git log --pretty=format:"%h %an %s %ar"
# %h = short hash, %an = author name, %s = subject, %ar = relative date
git log --pretty=format:"%C(yellow)%h%Creset %C(cyan)%an%Creset %s"

# Show commits in one branch but not another
git log main..feature              # in feature, not in main
git log feature..main              # in main, not in feature
git log main...feature             # in either but not both (symmetric diff)

# Show merge commits only
git log --merges

# Exclude merge commits
git log --no-merges
```

---

## 21. git reflog — Your Safety Net

The reflog (reference log) records **every change to HEAD** and every branch pointer — not just commits. It is your recovery mechanism when things go wrong.

Reflog is **local only** — it is not pushed to remote. Entries expire after 90 days by default (configurable). This is your time window for recovery.

```bash
# Show HEAD reflog
git reflog
# or equivalently:
git reflog show HEAD

# Output:
# abc123 HEAD@{0}: commit: feat: add login
# def456 HEAD@{1}: rebase finished: onto xyz789
# 789abc HEAD@{2}: checkout: moving from feature to main
# 012def HEAD@{3}: reset: moving to HEAD~3

# Show reflog for a specific branch
git reflog show main
git reflog show feature-x

# Show reflog with dates
git reflog --date=iso
git reflog --date=relative

# Recover a dropped commit (e.g., after git reset --hard)
git reflog                            # find the commit hash
git reset --hard abc123               # restore to that commit
git switch -c recovery-branch abc123  # or recover as new branch

# Recover a deleted branch
git reflog                            # find the last commit of deleted branch
git switch -c recovered-branch abc123 # recreate branch at that commit

# Expire old reflog entries manually
git reflog expire --expire=30.days refs/heads/main
git reflog expire --expire-unreachable=now --all
git gc    # garbage collect unreachable objects
```

### Reflog Syntax

```bash
HEAD@{0}     # current HEAD
HEAD@{1}     # HEAD one step ago
HEAD@{5}     # HEAD five steps ago
main@{2}     # main two steps ago
HEAD@{1 hour ago}    # time-based
HEAD@{yesterday}
HEAD@{2024-01-15}
```

---

## 22. Submodules

Submodules allow a Git repository to contain another Git repository as a subdirectory. Common for including libraries or components as exact versions.

### Adding a Submodule

```bash
# Add a submodule
git submodule add git@github.com:org/library.git vendor/library

# This creates:
# .gitmodules  ← tracks submodule config
# vendor/library/  ← the actual submodule (a separate git repo)

# The parent repo tracks vendor/library at a specific commit (gitlink)
git status
# Changes to be committed:
#   new file: .gitmodules
#   new file: vendor/library     ← recorded as a commit hash, not files
```

### Cloning a Repository with Submodules

```bash
# Clone and initialize all submodules in one step
git clone --recurse-submodules git@github.com:org/repo.git

# OR clone first, then initialize
git clone git@github.com:org/repo.git
cd repo
git submodule init      # register submodules from .gitmodules
git submodule update    # fetch and checkout the recorded commits

# Combined shortcut
git submodule update --init --recursive
```

### Updating Submodules

```bash
# Update all submodules to their recorded commits (after parent git pull)
git submodule update --recursive

# Pull latest from submodule's remote (update to newest commit)
git submodule update --remote vendor/library

# Perform operations in all submodules
git submodule foreach git pull origin main
git submodule foreach git status

# Show submodule status
git submodule status
```

### Removing a Submodule

```bash
# 1. Remove the submodule entry from .gitmodules
git submodule deinit vendor/library

# 2. Remove from .git/config
git rm vendor/library

# 3. Clean up
rm -rf .git/modules/vendor/library

git commit -m "chore: remove library submodule"
```

### Submodule Caveats

- Submodules add significant complexity — consider alternatives (Go modules, npm, package managers)
- Forgetting `--recurse-submodules` on clone/pull is the most common mistake
- Updating the pinned commit in a submodule requires a commit in the parent repo
- Developers must consciously update submodules — they don't auto-update with `git pull`

---

## 23. Worktrees

Worktrees allow you to check out multiple branches simultaneously in separate directories, all sharing the same `.git` directory (and thus the same object store and refs).

```bash
# Add a new worktree at a path, checking out a branch
git worktree add ../project-hotfix hotfix-1.2
git worktree add ../project-review feature-auth

# Add a new worktree with a new branch
git worktree add -b feature-xyz ../project-xyz main

# List all worktrees
git worktree list
# /home/user/project          abc123 [main]
# /home/user/project-hotfix   def456 [hotfix-1.2]
# /home/user/project-review   789abc [feature-auth]

# Remove a worktree
git worktree remove ../project-hotfix
git worktree remove --force ../project-hotfix  # even with uncommitted changes

# Clean up stale worktree metadata
git worktree prune
```

**When to use worktrees:**
- You need to review or test another branch without stashing your current work
- Running a long build or test on a different branch while editing in the main tree
- Working on a hotfix while your main worktree has deep in-progress work

**Constraints:**
- A branch can only be checked out in ONE worktree at a time
- Worktrees share the same `.git` directory — operations on refs affect all worktrees

---

## 24. Hooks — Automating at Git Events

Git hooks are scripts in `.git/hooks/` that Git runs automatically at specific events. They are not versioned in the repository by default (`.git/` is not committed).

### Hook Locations

```
.git/hooks/
  pre-commit          ← runs before commit (return non-zero to abort)
  prepare-commit-msg  ← runs before commit message editor opens
  commit-msg          ← runs after commit message is entered (validate format)
  post-commit         ← runs after commit (for notifications, etc.)
  pre-push            ← runs before push (return non-zero to abort push)
  pre-rebase          ← runs before rebase starts
  post-checkout       ← runs after git checkout/switch
  post-merge          ← runs after git merge
  pre-receive         ← server-side: runs before push is accepted
  update              ← server-side: runs once per branch pushed
  post-receive        ← server-side: runs after push is accepted (for CI triggers)
  post-update         ← server-side: similar to post-receive
```

### Example: pre-commit Hook

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Run tests before allowing commit
echo "Running tests..."
go test ./... 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR: Tests failed. Commit aborted."
    exit 1
fi

# Run linter
golangci-lint run ./...
if [ $? -ne 0 ]; then
    echo "ERROR: Linting failed. Commit aborted."
    exit 1
fi

echo "All checks passed."
exit 0
```

```bash
# Make it executable
chmod +x .git/hooks/pre-commit
```

### Example: commit-msg Hook (Conventional Commits Enforcement)

```bash
#!/bin/bash
# .git/hooks/commit-msg

commit_msg=$(cat "$1")
pattern="^(feat|fix|docs|style|refactor|perf|test|chore|ci|build)(\(.+\))?: .{1,72}"

if ! echo "$commit_msg" | grep -qE "$pattern"; then
    echo "ERROR: Commit message does not follow Conventional Commits format."
    echo "Expected: type(scope): description"
    echo "Example:  feat(auth): add JWT validation middleware"
    exit 1
fi
exit 0
```

### Sharing Hooks Across the Team

Since `.git/hooks/` is not versioned, use one of these approaches:

```bash
# Approach 1: Store hooks in repo, configure Git to use them
mkdir -p .githooks
cp .git/hooks/pre-commit .githooks/pre-commit
git config core.hooksPath .githooks    # tell Git to use this directory
# Each developer must run this config command

# Approach 2: Use a hook manager (Husky for JS, pre-commit for Python/any)
# pre-commit: https://pre-commit.com
pip install pre-commit
# Create .pre-commit-config.yaml in repo root
pre-commit install    # installs hooks into .git/hooks/
```

### Bypassing Hooks (Emergency Use Only)

```bash
git commit --no-verify -m "emergency: bypass hooks"
git push --no-verify
```

---

## 25. gitignore, gitattributes, gitconfig

### .gitignore — Excluding Files

`.gitignore` patterns tell Git to ignore matching files and directories.

```gitignore
# Comments start with #

# Ignore a specific file
.env
secrets.json

# Ignore all files with extension
*.log
*.tmp
*.pyc

# Ignore a directory
node_modules/
vendor/
dist/
build/

# Ignore files matching pattern in any directory
**/.DS_Store
**/__pycache__/

# Ignore only in the root directory (leading slash)
/config.local.yaml

# Negate a pattern (track despite earlier ignore)
!vendor/important-file.go

# Ignore everything in a directory except certain files
logs/*
!logs/.gitkeep    # keep the directory structure with empty placeholder

# Wildcard: * matches anything except /
# **  matches anything including /
src/**/*.test.js   # all .test.js files under src/
```

**Scope and precedence:**
1. `.gitignore` in the same directory (and all parents up to root)
2. `$GIT_DIR/info/exclude` (per-repo, not committed)
3. `core.excludesfile` global ignore file (`~/.gitignore_global`)

```bash
# Check why a file is ignored
git check-ignore -v filename

# Show all ignored files
git status --ignored

# Force-add an ignored file (bypass .gitignore)
git add -f important-but-ignored.file
```

### Global .gitignore

```bash
# Create global ignore file
cat > ~/.gitignore_global << 'EOF'
# OS files
.DS_Store
Thumbs.db

# Editor files
.vscode/
.idea/
*.swp
*.swo
*~

# Language artifacts
*.pyc
__pycache__/
*.class
*.o
*.so
*.dylib

# Environment files
.env
.env.local

# Build artifacts
dist/
build/
out/
EOF

git config --global core.excludesfile ~/.gitignore_global
```

### .gitattributes — Per-File Git Settings

`.gitattributes` configures Git behavior on a per-file-pattern basis. Committed into the repo.

```gitattributes
# Set default behavior: normalize line endings
* text=auto

# Force Unix line endings for these files
*.go   text eol=lf
*.sh   text eol=lf
*.yaml text eol=lf

# Force Windows line endings
*.bat  text eol=crlf

# Mark binary files (don't attempt line-ending conversion or diff)
*.png  binary
*.jpg  binary
*.pdf  binary
*.exe  binary
*.zip  binary

# Custom diff driver for Go files
*.go   diff=golang

# Mark files that should not be included in archives (git archive)
.gitignore  export-ignore
.gitattributes export-ignore
tests/ export-ignore

# Use linguist to classify files for GitHub syntax highlighting
*.go linguist-language=Go
docs/*.md linguist-documentation=true
vendor/** linguist-vendored=true
```

---

## 26. GitHub-Specific Concepts

### Forks

A **fork** is a server-side copy of a repository under your own account. Used for contributing to projects you don't have write access to.

Workflow:
1. Fork the repository on GitHub (creates `github.com/you/repo`)
2. Clone your fork: `git clone git@github.com:you/repo.git`
3. Add upstream: `git remote add upstream git@github.com:original-org/repo.git`
4. Keep fork in sync: `git fetch upstream && git rebase upstream/main`
5. Push your branch to your fork: `git push origin feature-branch`
6. Open a Pull Request from your fork to the original

```bash
# Typical fork workflow
git clone git@github.com:you/forked-repo.git
cd forked-repo
git remote add upstream git@github.com:original-org/repo.git

# Keep your fork current
git fetch upstream
git switch main
git rebase upstream/main
git push origin main     # update your fork's main

# Work on a feature
git switch -c my-feature
# ... make changes ...
git push -u origin my-feature
# Open PR on GitHub
```

### Pull Requests (PRs)

A Pull Request is a **GitHub concept** (not Git itself). It is a proposal to merge changes from one branch into another, with a structured review interface.

A PR includes:
- A diff of all changes
- A comment thread
- Review approvals/rejections
- Status checks (CI/CD results)
- Labels, assignees, linked issues

```bash
# From CLI with GitHub CLI (gh)
gh pr create --title "feat: add authentication" --body "Implements JWT auth"
gh pr list
gh pr view 42
gh pr merge 42 --squash
gh pr checkout 42    # check out a PR locally
```

### GitHub Actions (CI/CD)

GitHub Actions runs automated workflows triggered by Git events. Defined in `.github/workflows/*.yml`:

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'
      - run: go test ./...
      - run: go vet ./...
```

### Branch Protection Rules

Configure in GitHub Settings → Branches:
- Require pull request reviews before merging
- Require status checks to pass (CI)
- Require branches to be up to date before merging
- Require conversation resolution
- Restrict who can push to the branch
- Require signed commits
- Prevent force pushes
- Prevent branch deletion

### GitHub Releases

Releases are GitHub's way of packaging versioned software. They build on Git tags:

```bash
# Create an annotated tag and push it
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0

# Then on GitHub: create a Release from this tag
# Or via CLI:
gh release create v1.0.0 --title "Version 1.0.0" --notes "Release notes here"
gh release create v1.0.0 ./dist/binary-linux-amd64  # attach artifacts
```

---

## 27. Branching Strategies and Workflows

### GitHub Flow (Simplest)

Best for: teams doing continuous deployment, smaller projects.

```
main  ──────────────────────────────────────────► (always deployable)
         │              │ merge via PR
         ▼              │
    feature-x ─────────┘
         │              │ merge via PR
         ▼              │
    bugfix-99 ──────────┘
```

Rules:
1. `main` is always deployable
2. Work in feature branches, branched from `main`
3. Open a PR early, push often
4. Merge via PR after review + CI passes
5. Deploy immediately after merging to `main`

### Git Flow (More Complex)

Best for: projects with versioned releases, longer release cycles.

```
main ────────────────────────────────── v1.0 ──── v2.0
       ▲                                  ▲
develop ──────────────────────────────────────
         │         │         │
    feature-1  feature-2  feature-3
         │
    release/1.0 ──────────────────────────┘
         │
    hotfix/1.0.1 ────────────────────────┐
                                         ▼ (also merged back to develop)
```

Branches:
- `main` — production-ready code only, tagged at each release
- `develop` — integration branch, the "next release" in progress
- `feature/*` — branched from develop, merged back to develop
- `release/*` — branched from develop for release prep (bugfixes only), merged to main + develop
- `hotfix/*` — branched from main for emergency fixes, merged to main + develop

### Trunk-Based Development

Best for: high-velocity teams, Google-scale engineering.

```
main (trunk) ────────────────────────────────────────►
     ▲   ▲   ▲   ▲   ▲   ▲   ▲   ▲   ▲   ▲   ▲
  short-lived feature branches (hours, not days)
  feature flags control visibility of in-progress work
```

Rules:
- All developers integrate to `main` at least once daily
- Feature branches live for hours or 1-2 days maximum
- Feature flags (runtime toggles) hide incomplete work from users
- Heavy reliance on CI — main must never break

### Forking Workflow (Open Source)

Each contributor forks the project; all contributions come via PRs from forks:
- Upstream maintainers never give write access to contributors
- Contributors can never push directly to the main repo
- All changes reviewed via pull request

---

## 28. Commit Message Conventions

### Why Commit Messages Matter

A good commit message is documentation. `git log` becomes a changelog. `git blame` becomes understandable. Future you (and colleagues) can understand not just WHAT changed but WHY.

### The Seven Rules of Great Commit Messages

1. Separate subject from body with a blank line
2. Limit the subject line to 72 characters
3. Capitalize the subject line
4. Do not end the subject line with a period
5. Use the imperative mood ("Add feature" not "Added feature" or "Adds feature")
6. Wrap the body at 72 characters
7. Use the body to explain WHAT and WHY, not HOW

```
feat(auth): add JWT validation middleware

Implement RS256 JWT validation for all API endpoints. The middleware
validates token signature, expiry, issuer, and audience claims.

Previously, authentication relied on session cookies which don't work
for our mobile clients and third-party integrations.

The middleware short-circuits at the router level before any handler
is invoked, so no authentication logic is needed in individual handlers.

Refs: #142
Co-authored-by: Bob Smith <bob@example.com>
```

### Conventional Commits Specification

A widely adopted format: `type(scope): description`

```
type(scope): short description

optional body

optional footer(s)
```

**Types:**
- `feat` — new feature (correlates with MINOR in SemVer)
- `fix` — bug fix (correlates with PATCH)
- `docs` — documentation only
- `style` — formatting, missing semicolons (no code logic change)
- `refactor` — code restructuring (no feature, no fix)
- `perf` — performance improvement
- `test` — adding/fixing tests
- `chore` — build process, dependency updates, CI configuration
- `ci` — changes to CI configuration files
- `build` — changes affecting the build system
- `revert` — reverts a previous commit

**Breaking changes:**
```
feat!: change authentication API

BREAKING CHANGE: The /auth/token endpoint now requires client_id parameter.
Clients must update their requests to include this field.
```

```bash
# Examples
git commit -m "feat(api): add rate limiting to authentication endpoints"
git commit -m "fix(db): handle null pointer in user query"
git commit -m "docs: update deployment guide for Kubernetes"
git commit -m "perf(cache): replace in-memory map with sync.Map"
git commit -m "chore(deps): update go.mod dependencies"
```

---

## 29. Conflict Resolution — In Depth

### What Is a Merge Conflict?

A conflict occurs when Git cannot automatically determine how to combine changes from two branches to the same lines in the same file. Git requires human judgment.

Git creates conflict markers in the file:

```go
func Authenticate(token string) (bool, error) {
<<<<<<< HEAD
    // Current branch: validate expiry first
    if isExpired(token) {
        return false, ErrTokenExpired
    }
    return validateSignature(token)
||||||| base (with diff3 conflictstyle)
    // Common ancestor version
    return validateToken(token)
=======
    // Incoming branch: validate signature first
    if !validateSignature(token) {
        return false, ErrInvalidSignature
    }
    return validateExpiry(token)
>>>>>>> feature/improved-auth
```

With `merge.conflictstyle = diff3` (recommended):
- `<<<<<<< HEAD` to `|||||||` — your current branch version
- `||||||| base` to `=======` — the common ancestor version (what both sides started from)
- `=======` to `>>>>>>>` — the incoming branch version

### Resolving Conflicts

```bash
# Step 1: See which files have conflicts
git status
git diff --name-only --diff-filter=U    # list conflicted files

# Step 2: Resolve each conflict
# Option A: Edit manually — remove markers, write the correct code
# Option B: Use a merge tool
git mergetool                    # opens configured tool for each conflict
git mergetool --tool=vimdiff
git mergetool --tool=code        # VSCode (configure as merge tool)

# Option C: Accept one side entirely
git checkout --ours   conflicted-file.go     # use your version
git checkout --theirs conflicted-file.go     # use incoming version
# Modern:
git restore --ours   conflicted-file.go
git restore --theirs conflicted-file.go

# Step 3: Stage the resolved file
git add conflicted-file.go

# Step 4: Continue (after all conflicts resolved)
git merge --continue    # or git commit
git rebase --continue   # if conflict during rebase
git cherry-pick --continue
```

### VSCode as Merge Tool

```bash
git config --global merge.tool vscode
git config --global mergetool.vscode.cmd 'code --wait $MERGED'
git mergetool    # opens VSCode with Accept Current/Incoming/Both buttons
```

### Understanding Both Sides

Before resolving, understand the intent of both changes:

```bash
# See what your branch changed in the conflicting file
git log HEAD --oneline -- conflicted-file.go

# See what their branch changed
git log MERGE_HEAD --oneline -- conflicted-file.go

# See the full diff of the conflict from both sides
git diff HEAD MERGE_HEAD -- conflicted-file.go
```

### rerere — Reuse Recorded Resolution

If you enable `rerere` (Reuse Recorded Resolution), Git remembers how you resolved a conflict. If it sees the same conflict again (e.g., after rebasing repeatedly), it auto-resolves it.

```bash
git config --global rerere.enabled true

# List recorded resolutions
git rerere status
git rerere diff    # show recorded resolution

# Clear a bad recording
git rerere forget conflicted-file.go
```

---

## 30. Security Considerations in Git

### Commit Signing with GPG

Signed commits cryptographically prove that the commit was made by the holder of a specific GPG key. GitHub displays a "Verified" badge.

```bash
# Generate a GPG key (if you don't have one)
gpg --full-generate-key
# Choose: RSA 4096, no expiry (or 2 years), fill in your email

# List your keys
gpg --list-secret-keys --keyid-format=long

# Get key ID (16-char hex after "sec   rsa4096/")
gpg --list-secret-keys --keyid-format=long | grep sec
# sec   rsa4096/ABCDEF1234567890 2024-01-01

# Export public key to add to GitHub
gpg --armor --export ABCDEF1234567890

# Configure Git to sign commits
git config --global user.signingkey ABCDEF1234567890
git config --global commit.gpgsign true
git config --global tag.gpgsign true

# Sign a specific commit (without global setting)
git commit -S -m "signed commit"

# Verify signatures
git log --show-signature
git verify-commit HEAD
git verify-tag v1.0.0
```

### SSH Signing (Modern Alternative to GPG)

Git 2.34+ supports using SSH keys for signing, which is simpler than GPG:

```bash
# Use your existing SSH key for signing
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true

# Create allowed signers file for verification
echo "you@example.com $(cat ~/.ssh/id_ed25519.pub)" >> ~/.ssh/allowed_signers
git config --global gpg.ssh.allowedSignersFile ~/.ssh/allowed_signers

# Verify
git verify-commit HEAD
```

### Never Commit Secrets

```bash
# BEFORE committing, check for secrets
git diff --staged | grep -iE '(password|secret|key|token|api_key)'

# Use tools: gitleaks, truffleHog, detect-secrets
# Install gitleaks:
go install github.com/gitleaks/gitleaks/v8@latest

# Scan a repo
gitleaks detect --source . --verbose

# Scan staged changes (as pre-commit hook)
gitleaks protect --staged -v
```

### Removing Accidentally Committed Secrets

If you committed a secret and pushed it — assume it is compromised. Rotate it immediately. Then clean the history:

```bash
# Option 1: git-filter-repo (recommended, faster than BFG)
pip install git-filter-repo
git filter-repo --path secrets.json --invert-paths   # remove file from all history
git filter-repo --replace-text <(echo 'my-secret-token==>REMOVED')

# Option 2: BFG Repo Cleaner (Java)
java -jar bfg.jar --delete-files secrets.json
java -jar bfg.jar --replace-text passwords.txt

# After either: force push ALL branches
git push --force --all
git push --force --tags
# GitHub: contact support to purge from their caches
```

### SSH Key Best Practices

```bash
# Generate ED25519 key (preferred over RSA now)
ssh-keygen -t ed25519 -C "jane@example.com" -f ~/.ssh/github_ed25519

# Or RSA 4096 for maximum compatibility
ssh-keygen -t rsa -b 4096 -C "jane@example.com" -f ~/.ssh/github_rsa

# Add to SSH agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/github_ed25519

# ~/.ssh/config
cat >> ~/.ssh/config << EOF
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_ed25519
    AddKeysToAgent yes
EOF

# Test connection
ssh -T git@github.com
# Hi Jane! You've successfully authenticated...

# Verify GitHub's SSH fingerprints (don't just accept unknown hosts)
# https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/githubs-ssh-key-fingerprints
```

### .gitignore for Security

```gitignore
# Secrets and credentials
.env
.env.*
!.env.example
*.pem
*.key
*.p12
*.pfx
id_rsa
id_ed25519
*_rsa
*_ed25519
credentials.json
secrets.yaml
secrets.json
kubeconfig
*.kubeconfig
service-account-key.json
```

### Dependency Security in Git Workflows

```bash
# Sign your commits and tags for release verification
# Use branch protection to require signed commits
# Use Dependabot / Renovate to auto-PR dependency updates
# Use SBOM generation in CI (cyclonedx, syft)

# GitHub Dependabot configuration: .github/dependabot.yml
cat > .github/dependabot.yml << EOF
version: 2
updates:
  - package-ecosystem: "gomod"
    directory: "/"
    schedule:
      interval: "weekly"
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
EOF
```

---

## 31. Performance and Large Repositories

### Partial Clone

Download only the objects you need, fetching others on demand:

```bash
# Clone without blobs (fetch file content on demand)
git clone --filter=blob:none git@github.com:org/large-repo.git

# Clone without trees (very aggressive — mainly for CI)
git clone --filter=tree:0 git@github.com:org/large-repo.git

# Blobless clone (no blob content) + shallow
git clone --filter=blob:none --depth=1 git@github.com:org/large-repo.git
```

### Sparse Checkout

Work with only a subset of the repository's files:

```bash
# Enable sparse checkout on an existing clone
git sparse-checkout init --cone
git sparse-checkout set src/module-a src/module-b

# Or clone with sparse checkout
git clone --sparse git@github.com:org/monorepo.git
cd monorepo
git sparse-checkout set services/auth services/api
```

### Git LFS (Large File Storage)

For large binary files (images, datasets, compiled artifacts):

```bash
# Install git-lfs
sudo apt install git-lfs
git lfs install   # per-user setup

# Track large file types
git lfs track "*.psd"
git lfs track "*.png"
git lfs track "*.zip"
git add .gitattributes   # .gitattributes is updated by lfs track
git commit -m "chore: configure git-lfs for binary files"

# Check what's tracked
git lfs ls-files
git lfs track
```

### Repository Maintenance

```bash
# Garbage collect unreachable objects
git gc

# Aggressive GC (slower, more compression)
git gc --aggressive --prune=now

# Repack for performance
git repack -a -d -f --depth=250 --window=250

# Check repository integrity
git fsck --full

# Count objects
git count-objects -vH
```

---

## 32. VSCode Git Integration

VSCode has excellent built-in Git support and the GitLens extension adds significant depth.

### Built-in Source Control Panel (Ctrl+Shift+G)

- **Changes** section: unstaged modifications (click file to see diff)
- **Staged Changes** section: files staged for commit
- `+` icon: stage file
- `-` icon: unstage file
- Commit message box + checkmark: commit
- `...` menu: access to all Git operations

### Keyboard Shortcuts

| Action | Shortcut |
|---|---|
| Open Source Control | `Ctrl+Shift+G` |
| Stage file (in diff) | `Ctrl+Shift+A` |
| Open terminal | `Ctrl+\`` |
| Stage all changes | Click `+` on "Changes" header |
| View Git log | `Ctrl+Shift+P` → "Git: View History" |
| Checkout branch | `Ctrl+Shift+P` → "Git: Checkout to..." |

### Recommended Extensions

```
GitLens (GitKraken)   — blame, history, compare, worktrees
Git Graph             — visual branch graph
Git History           — file and line history
GitHub Pull Requests  — manage PRs from within VSCode
```

### VSCode as Difftool

```bash
git config --global diff.tool vscode
git config --global difftool.vscode.cmd 'code --wait --diff $LOCAL $REMOTE'
git difftool HEAD~1 HEAD    # opens VSCode diff for each changed file
```

### VSCode as Merge Tool

```bash
git config --global merge.tool vscode
git config --global mergetool.vscode.cmd 'code --wait $MERGED'
git mergetool    # during a conflict, opens VSCode with merge editor
```

VSCode's 3-way merge editor shows: Current (ours), Incoming (theirs), Result (bottom). You can accept current, incoming, both, or edit manually.

### .vscode/settings.json for Git

```json
{
    "git.enableSmartCommit": true,
    "git.autofetch": true,
    "git.confirmSync": false,
    "git.defaultCloneDirectory": "~/projects",
    "gitlens.currentLine.enabled": true,
    "gitlens.hovers.currentLine.over": "line",
    "editor.inlineSuggest.enabled": true
}
```

---

## 33. Common Mistakes and How to Fix Them

### 1. Committed to the Wrong Branch

```bash
# Undo the commit on wrong branch (keep changes)
git reset --soft HEAD~1
# Switch to correct branch
git switch correct-branch
# Commit there
git commit -m "same message"

# OR: cherry-pick to correct branch, then remove from wrong branch
git log --oneline -3   # note the commit hash
git switch correct-branch
git cherry-pick abc123   # apply commit here
git switch wrong-branch
git reset --hard HEAD~1  # remove commit (if unpushed)
```

### 2. Committed Sensitive Data (Secret/Password)

```bash
# IMMEDIATELY rotate the secret/token/password — it's compromised
# Then remove from history (see Security section)
# Notify your team; force-push all branches
```

### 3. Pushed to Main Directly

```bash
# If protected: GitHub prevents this (configure branch protection!)
# If not protected:
git reset --hard HEAD~1    # undo local
git push --force-with-lease origin main   # update remote
# Alert team members who may have pulled
```

### 4. Accidentally Deleted a Branch

```bash
# Find the last commit of the deleted branch
git reflog | grep feature-x
# abc123 HEAD@{5}: checkout: moving from feature-x to main

# Recreate the branch
git switch -c feature-x abc123
```

### 5. Accidentally ran git reset --hard

```bash
# Your commits are in the reflog for 90 days
git reflog
# Find the commit just before the reset
# e.g., abc123 HEAD@{2}: commit: your work

git reset --hard abc123   # restore to that state
# Or create a branch there:
git switch -c recovery-branch abc123
```

### 6. Merge Conflict in the Middle of Rebase

```bash
# Don't panic — resolve the conflict, then continue
git status               # see which file conflicts
# Edit the file to resolve
git add resolved-file.go
git rebase --continue    # continue replaying commits
# OR abort entirely:
git rebase --abort       # returns to pre-rebase state exactly
```

### 7. Pushed Commits That Need Rewriting

```bash
# You pushed commits that need to be changed (messy history on PR branch)
# Rewrite locally:
git rebase -i origin/main   # interactive rebase against remote main

# Force push (only OK for your feature branch, not shared branches):
git push --force-with-lease origin your-feature-branch
```

### 8. git pull Created Unwanted Merge Commit

```bash
# After accidental merge commit from git pull:
git reset --hard ORIG_HEAD   # ORIG_HEAD is set before dangerous operations

# Configure to avoid this in future:
git config --global pull.rebase true
```

### 9. Large File Accidentally Committed

```bash
# Remove from index before push
git rm --cached large-file.bin
echo "large-file.bin" >> .gitignore
git commit -m "chore: remove large file, add to gitignore"

# If already pushed — must rewrite history with git-filter-repo
```

### 10. Detached HEAD Confusion

```bash
# You're in detached HEAD and want to keep your work
git switch -c new-branch-name   # save your commits in a branch

# You're in detached HEAD and want to discard
git switch main                  # just switch away (commits become unreachable)
```

### 11. Forgot to Pull Before Push (Rejected Push)

```bash
# Push rejected: remote has new commits
git push
# ! [rejected] main -> main (fetch first)

# Solution with rebase (preferred):
git pull --rebase
git push

# Solution with merge:
git pull
git push
```

### 12. Wrong Email in Commits

```bash
# Fix the last commit
git commit --amend --reset-author

# Fix multiple commits (interactive rebase):
git rebase -i HEAD~5
# Mark all as 'edit', then for each:
git commit --amend --reset-author
git rebase --continue

# Fix all commits with filter-repo
git filter-repo --email-callback '
    return email if email != b"wrong@email.com" else b"correct@email.com"
'
```

---

## 34. Quick Reference Cheatsheet

### Setup

```bash
git config --global user.name "Name"
git config --global user.email "email"
git config --global init.defaultBranch main
git config --global pull.rebase true
git config --list
```

### Creating Repositories

```bash
git init                    # new local repo
git clone <url>             # clone remote repo
git clone --depth=1 <url>   # shallow clone
```

### Daily Workflow

```bash
git status -sb              # see state
git add <file>              # stage file
git add -p                  # stage interactively by hunk
git add -A                  # stage everything
git commit -m "msg"         # commit
git commit --amend          # fix last commit
git log --oneline --graph   # see history
git diff                    # unstaged changes
git diff --staged           # staged changes
```

### Branches

```bash
git branch                  # list branches
git switch -c <branch>      # create + switch
git switch <branch>         # switch
git branch -d <branch>      # delete (safe)
git branch -D <branch>      # delete (force)
git branch -m <new-name>    # rename current branch
```

### Remotes

```bash
git remote -v               # list remotes
git remote add origin <url> # add remote
git fetch origin            # download (no merge)
git pull --rebase           # fetch + rebase
git push -u origin <branch> # push + set upstream
git push --force-with-lease # safe force push
```

### Stash

```bash
git stash push -m "msg"     # stash with message
git stash list              # list stashes
git stash pop               # apply + remove top
git stash apply stash@{2}   # apply specific
git stash drop stash@{1}    # remove specific
git stash branch <branch>   # apply to new branch
```

### Merging and Rebasing

```bash
git merge <branch>          # merge into current
git merge --no-ff <branch>  # merge with merge commit
git merge --abort           # abort merge
git rebase main             # rebase onto main
git rebase -i HEAD~5        # interactive rebase (5 commits)
git rebase --continue       # after resolving conflict
git rebase --abort          # abort rebase
```

### Undoing

```bash
git restore <file>          # discard working dir changes
git restore --staged <file> # unstage
git reset --soft HEAD~1     # undo commit, keep staged
git reset --mixed HEAD~1    # undo commit, keep unstaged
git reset --hard HEAD~1     # undo commit, discard changes
git revert <commit>         # safe undo (new commit)
git cherry-pick <commit>    # apply commit to current branch
```

### Inspection

```bash
git log -p -- <file>        # history + diffs for file
git blame <file>            # who changed each line
git bisect start            # start binary search
git reflog                  # all HEAD movements
git show <commit>           # show commit details
git diff <branch1>..<branch2>  # compare branches
```

### Tags

```bash
git tag -a v1.0.0 -m "msg"  # annotated tag
git tag -l                  # list tags
git push origin --tags       # push all tags
git push origin v1.0.0       # push specific tag
git tag -d v1.0.0            # delete local tag
```

### Advanced

```bash
git submodule update --init --recursive
git worktree add <path> <branch>
git bisect run <script>
git filter-repo --path <file> --invert-paths
git reflog expire --expire=now --all && git gc --prune=now
```

---

## Appendix: Git Internals Summary

```
Repository = Object Store + References
  Object Store:
    blob     = file content (no name)
    tree     = directory listing (names + modes + blob/tree refs)
    commit   = snapshot (tree ref + parent refs + author + message)
    tag      = named pointer with metadata

  References:
    refs/heads/<name>         = local branch
    refs/remotes/<r>/<name>   = remote-tracking branch
    refs/tags/<name>          = tag
    HEAD                      = current branch or commit

  Index:
    .git/index                = proposed next commit (staging area)

Three trees:
    Working Dir → (git add) → Index → (git commit) → HEAD
    HEAD → (git reset) → Index → (git restore --staged) → Working Dir

History = DAG (Directed Acyclic Graph) of commit objects
    Each commit points to parent(s)
    Branches are just movable pointers into this graph
    Merges = commits with 2+ parents
    Tags = immutable pointers
```

---

*End of Guide — Last updated for Git 2.44 (2024)*
