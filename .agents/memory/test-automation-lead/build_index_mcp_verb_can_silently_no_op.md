---
name: build_index MCP verb can silently no-op — verify mtime, don't trust the success message
description: mcp__onetest-tms__build_index reported "wrote index.json, N cases indexed" but the file on disk in the sibling clone never changed (cwd mismatch); check mtime before trusting it, fall back to the packaged _index.py script
type: feedback
---

Hit on ELITEA-2037 (issue #474). Called `mcp__onetest-tms__build_index` with
`repo: "EliteaAI/onetest-ai-tm-Elitea"` after hand-editing the case markdown's
frontmatter. It returned a clean success: "✓ wrote index.json — 2743 cases
indexed". But `ls -la index.json` in the actual sibling clone
(`../onetest-ai-tm-Elitea`) showed an mtime from **before** my markdown edit —
the tool had not touched that file. A repo-wide `find` for any `index.json`
modified since the call turned up nothing either; wherever the MCP server's
`build_index` actually wrote (if anywhere), it wasn't discoverable from this
checkout. `.mcp.json` sets no explicit `cwd` for the `onetest-tms` server, so
its working directory is inherited from wherever Claude Code was launched
(`elitea-testing-public/`, not the TMS sibling) — plausible root cause, not
confirmed.

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
