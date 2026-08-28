---
name: The Bash tool's shell is zsh — unquoted $VAR does NOT word-split
description: F="a.py b.py"; cmd $F passes ONE argument; silently produced a bogus "no new lint" result
type: feedback
aliases: [zsh word splitting, multi-file variable, ruff one path, shell array]
tags: [area/shell, type/hazard]
created: 2026-08-28
updated: 2026-08-28
---

## What happened

```bash
F="config.py api/client.py api/__init__.py tests/.../test_x.py"
ruff check $F --output-format=concise
```

Under bash this passes four paths. **Under zsh it passes one** — the whole
string as a single filename. Ruff answered:

```
config.py api/client.py api/__init__.py tests/.../test_x.py:: E902 No such file or directory
```

Because I was diffing "before" against "after" output, both sides produced the
same E902 line and the comparison reported **"IDENTICAL — zero new lint
findings"**. A completely fabricated pass, from a check that never ran.

## The rules that follow

- **Write the paths out literally**, or use a zsh array (`F=(a.py b.py)` then
  `cmd $F`), or `set -o shwordsplit`. Do not rely on `$VAR` splitting.
- **Sanity-check any tool's output for the shape you expect before trusting a
  comparison built on it.** A 4-file ruff run producing 2 output lines should
  have stopped me immediately; instead the diff-of-two-broken-runs looked like
  success. When a verification comes back clean, confirm it actually *ran*.

Related: [[git_checkout_ref_path_overwrites_the_index]]
