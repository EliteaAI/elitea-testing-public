---
name: build_index MCP verb can silently no-op — verify mtime, don't trust the success message
description: passing repo: to any onetest-tms MCP tool (build_index included) clones/writes a SEPARATE checkout at ~/.onetest-workspaces/<owner>/<name> — omit repo entirely so it uses $OT_REPO_ROOT (the real sibling clone)
type: feedback
---

**ROOT CAUSE CONFIRMED (2026-08-05, #784/ELITEA-2277), reading `server.js`
itself:** every `onetest-tms` MCP tool takes an optional `repo` arg. When
given, `workspace(repo)` clones/pulls **`$OT_WORKSPACE/<owner>/<name>`**
(default `~/.onetest-workspaces/<owner>/<name>`) and runs the tool THERE —
a throwaway parallel checkout, not the sibling clone. When `repo` is
**omitted**, it uses `DEFAULT_CWD = process.env.OT_REPO_ROOT || …` — and
`OT_REPO_ROOT` is in fact set (confirmed via `ps eww -p <pid>`) to the real
`../onetest-ai-tm-Elitea` sibling. So the fix is trivial: **call
`build_index` (and every other onetest-tms tool) with NO `repo` argument.**
Passing `repo: "EliteaAI/onetest-ai-tm-Elitea"` looks like the obviously
correct explicit form and is exactly what silently misroutes the write.

If you already passed `repo:` and suspect this: `rm -rf
~/.onetest-workspaces/<owner>/<name>` to clear the stale parallel clone (it
will re-clone from whatever `main` was at the time and can otherwise mislead
a later accidental `repo:`-qualified call into reading/writing stale data
indefinitely), then re-run the tool bare.

**Original symptom (issue #474, before the cause was known):** Called
`mcp__onetest-tms__build_index` with `repo: "EliteaAI/onetest-ai-tm-Elitea"`
after hand-editing the case markdown's frontmatter. It returned a clean
success: "✓ wrote index.json — 2743 cases indexed". But `ls -la index.json`
in the actual sibling clone (`../onetest-ai-tm-Elitea`) showed an mtime from
**before** my markdown edit — the tool had not touched that file (it had
silently written to `~/.onetest-workspaces/EliteaAI/onetest-ai-tm-Elitea`
instead, per the confirmed cause above).

**Don't trust the tool's own "wrote index.json" / "N cases indexed" message as
proof of a real write.** Check `ls -la index.json` (or `git status`) in the
actual sibling clone immediately after the call — if the mtime is stale or
`git diff` is empty, the call was a no-op.

**Fallback that works:** run the packaged indexer script directly, from the
TMS sibling clone itself:
```bash
cd ../onetest-ai-tm-Elitea
python3 onetest-tms/scripts/_index.py --dir tests --out index.json
```
This is a **full rebuild** (rewrites every case's entry, not just yours) —
`tms_index_backwrite_surgical_not_full_rebuild.md` correctly warns against
committing that blind on a chronically-stale index (283+ cases of drift can
ride along silently). The mitigation is the same either way: **run
`git diff --stat index.json` (or read the diff) before committing**, and
confirm it only touches entries you can account for. In this instance the
diff was exactly 2 entries — mine (ELITEA-2037) and one genuinely-stale
leftover from an earlier session's back-write (ELITEA-2034, whose `.md`
frontmatter was already `ready`/`automated` but had never made it into
`index.json`) — small and legitimate enough to commit together. If the diff
had been large or touched entries with unclear/contradictory state, the
surgical single-entry Python edit from the other entry is still the right
tool; don't reach for the full rebuild as a default, only as a checked
fallback when the MCP verb has already failed you.

**Confirmed a 2nd time, #477/ELITEA-2040 (same session-day):** identical
no-op — mtime predated the call, `status`/`execution_type` still
`draft`/`manual` in `index.json` after the MCP tool reported "wrote
index.json, 2743 cases indexed". `_index.py` fallback fixed it in one shot,
diff scoped to exactly the one entry. This is now a **reliable, repeatable
failure of the MCP verb**, not a one-off — treat the mtime/git-diff check as
mandatory every time, not a suspicious-result-only step.

**Confirmed a 3rd time, #505/ELITEA-2068:** same no-op (2743 cases claimed,
`index.json` unchanged). Gotcha this time: my first `_index.py` invocation
used `--dir tests/automated-full-regression-ui` (the case's own subfolder,
seemed natural) and only indexed 697 cases — silently narrower than the
real tree. The script's own default is `--dir tests` (the *whole* tests/
tree, matching what the MCP tool's "2743 cases" count actually covers) — use
that default (or pass `--dir tests` explicitly), never a case's subfolder,
or the rebuild itself becomes a silent under-count.

**Confirmed a 4th time, #788/ELITEA-2280 (2026-08-05):** despite this entry
already documenting the root cause explicitly, I still typed
`build_index(repo="EliteaAI/onetest-ai-tm-Elitea")` out of habit (it reads as
the obviously-correct explicit form) and got the clean "2743 cases indexed"
success message. `ls -la index.json` in the real sibling showed the mtime
predated my call and the entry was still `draft`/`manual`/empty
`automation_test_id`. Re-ran with **zero args** — correct write, mtime
updated, diff scoped to exactly the one changed id. Lesson refined: reading
this entry in the abstract isn't enough to stop the habit — before EVERY
`build_index` call, actually check the call for a `repo:` key and delete it,
don't rely on remembering "I know about this bug already."
