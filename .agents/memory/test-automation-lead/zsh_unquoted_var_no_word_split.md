---
name: zsh does not word-split unquoted variables (unlike bash)
description: Multi-node-id pytest calls / multi-branch loops built as space-separated strings in $VAR collapse into ONE argument in zsh — use heredoc files + while-read, or literal arrays, not unquoted $VAR expansion
type: feedback
---

## What happened

Batch #1298 (2026-08-08): the Bash tool's shell is `/bin/zsh`, not bash.
Building a multi-line/multi-item variable (`NODES="a b c \` continuation, or
`BRANCHES="a b c"`) and then doing `pytest $NODES` or `for b in $BRANCHES`
unquoted did NOT split into separate words the way it would in bash — zsh
passed the whole thing as one argument. Symptoms: `pytest` reported "not
found: <one giant path with spaces in it>" for a multi-node-id gate run;
`git branch -D $BRANCHES` reported "branch '<all 13 branch names as one
string>' not found". `mapfile` (a bash builtin) also doesn't exist in zsh —
errors "command not found: mapfile".

## The fix that works reliably

Write the list to a file, one item per line, then either:
- `while IFS= read -r item; do ...; done < /tmp/list.txt` (loop), or
- `xargs` reading from **stdin** (BSD xargs on macOS has no `-a` flag —
  `cat file | xargs cmd`, not `xargs -a file cmd`).

Do not rely on unquoted `$VAR` splitting, `${arr[@]}` array literals typed
inline, or `mapfile`/`readarray` in this shell. A heredoc file + `while read`
or `xargs` (via a pipe) is the portable pattern that has actually worked
across this session's pytest multi-node-id gate runs and branch-cleanup
loops.

## Why this matters for THIS role specifically

The merge-gate step and batch branch cleanup are exactly the kind of
multi-item shell operations that hit this — a batch gate run needs N
node-ids passed together (so xdist/collection semantics match a real CI
invocation), and end-of-batch cleanup deletes many branches. Getting either
wrong either produces a misleading "no tests collected" run (which could be
mistaken for "the gate can't find anything, investigate the tests") or a
`git branch -D` error that looks like a real problem with the branch itself.
