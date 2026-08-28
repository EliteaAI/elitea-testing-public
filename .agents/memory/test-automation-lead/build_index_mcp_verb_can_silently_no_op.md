---
name: build_index MCP verb silently no-ops when you pass repo: — omit the argument
description: passing repo: to ANY onetest-tms MCP tool routes it to a throwaway clone at ~/.onetest-workspaces/<owner>/<name>; call it bare so it uses $OT_REPO_ROOT (the real sibling clone)
type: feedback
aliases: [build_index, onetest-tms, index.json, onetest-workspaces, correlate_results stale]
tags: [area/tms, type/trap]
created: 2026-08-05
updated: 2026-08-28
---

## The rule

**Call every `onetest-tms` MCP tool with NO `repo` argument.**

`server.js`: given `repo`, `workspace(repo)` clones/pulls
`~/.onetest-workspaces/<owner>/<name>` and runs the tool **there**. Omitted, it
uses `DEFAULT_CWD = process.env.OT_REPO_ROOT`, which is set to the real
`../onetest-ai-tm-Elitea` sibling.

```
build_index(repo="EliteaAI/onetest-ai-tm-Elitea")   # ← silently writes elsewhere, reports success
build_index()                                       # ← correct
```

`repo:` reads as the obviously-correct explicit form, which is exactly why this
keeps happening. **Confirmed 7 times (2026-08-05 → 2026-08-28), including twice
by agents who had already read this entry.** Reading it is not enough: before
sending the call, look at it and delete any `repo:` key.

## Verify the write — the success message proves nothing

`✓ wrote index.json — N cases indexed` is emitted regardless. In the *real*
sibling clone, immediately after:

```bash
ls -la index.json     # mtime must be after your call
git status            # must show index.json modified
```

Stale mtime / empty diff ⇒ it was a no-op. A tell: the reported case count is
lower than the real tree's (e.g. 2789 vs 3097) — that is the throwaway clone's
stale checkout, **not** evidence of index drift.

## Fallback when the verb has already failed you

```bash
cd ../onetest-ai-tm-Elitea
python3 onetest-tms/scripts/_index.py --dir tests --out index.json
```

- `--dir tests` (the script's default) or you silently under-count. Passing a
  case's own subfolder (e.g. `tests/automated-full-regression-ui`) indexed only
  697 of ~3000 cases and looked fine.
- Omitting `--out` prints the JSON to stdout instead of writing it.
- This is a **FULL rebuild**. Do not commit it blind for a single-case
  back-write — see [[tms_index_backwrite_surgical_not_full_rebuild]]. Always
  `git diff --numstat index.json` first and account for every entry it touches.

## Cleaning up a dirtied throwaway workspace

A `repo:`-qualified call leaves that clone behind and it accumulates drift
across sessions (found once carrying an uncommitted diff from a much earlier
session on top of a `main` several commits stale).

```bash
rm -rf ~/.onetest-workspaces/<owner>/<name>          # simplest
# or, to keep it:
cd ~/.onetest-workspaces/<owner>/<name>
git checkout -- . && git fetch origin && git reset --hard origin/main
```

Then re-call bare and confirm in the real sibling with
`grep -A5 '"id": "<CASE-ID>"' index.json`.

Related: [[tms_index_backwrite_surgical_not_full_rebuild]] · [[tms_backwrite_is_manual_git_edit_not_mcp_verb]] · [[onetest_index_json_drift_needs_periodic_rebuild]]
