
# Copilot / AI agent instructions — SDE-Notes

Purpose: help an automated coding agent be immediately productive in this repository by documenting the repository "big picture", conventions, and concrete examples of common edits.

1) Big picture
- This repository is a curated collection of engineering notes and tutorials (Markdown-first). Major topical folders include `dsa/`, `codeflow/`, `backend/`, `python/`, `rust/`, `system design/`, and many single-file notes. There is no build system or runtime code to execute in the tree — most artifacts are `.md` documents.
- Design intent: files are organized by topic rather than a single app; changes should preserve historical / topical organization and avoid moving many files unless consolidating duplicates.

2) Key files and directories (examples)
- `backend/` — notes about Django and PostgreSQL (e.g. `backend/django-core.md`, `backend/django-postgresql.md`).
- `dsa/` — algorithms, patterns and problem notes (e.g. `dsa/dsa.md`, `dsa/sliding window.md`).
- `codeflow/` — workflow notes and short how-tos (e.g. `codeflow/django-code-0.md`, `codeflow/coding properly.md`).
- Root `README.md` — short project title; keep small and high-level.

3) Repository-specific conventions
- File types: primarily Markdown. Preserve existing heading structure and fenced code blocks when editing.
- Filenames: many files include spaces and loose capitalization (e.g. `code safe.md`). Avoid renaming files unless requested — renames can break links and user expectations.
- Linking: use relative links between notes when adding cross-references. Prefer linking to the file path (e.g. `[Django notes](../backend/django-core.md)`).

4) Common agent tasks & examples (concrete)
- Add a short summary to a long note: open file (e.g. `dsa/dsa.md`), prepend a 2–4 line summary under the top-level heading.
- Canonicalize code blocks: add language tags to fenced blocks (```python, ```bash) when missing.
- Fix typos and clarify steps in HOWTOs — for example in `backend/django-core.md` keep Django command examples verbatim and add small clarifying notes.

5) Developer workflows / useful commands
- There is no specialised build or test runner. Typical workflow is git-based editing and review. Examples:
	- Search for relevant note: use ripgrep/ag (or VS Code global search) to find occurrences of a term.
	- Create a branch: `git checkout -b fix/<short-desc>`
	- Commit small, focused changes and open a PR to `main`.

6) What to avoid
- Don't rearrange the folder topology or mass-rename files without explicit instruction.
- Don't add compiled artifacts, notebooks, or large binaries; this repository is notes-first.

7) Integration points & external dependencies
- There are no code dependencies or CI workflows detected. If you plan to add a runnable example, create a small subfolder and include a short README and a `requirements.txt` / manifest.

8) When you need clarification
- If an edit could change meaning (restructure, rename, or delete), create a short draft or PR and ask the repository owner for confirmation.

If anything in these instructions is unclear or you want more detail on a particular folder or workflow, tell me which area and I'll expand the guidance or add examples.
