---
name: TMS back-write must git-add the case file only, never blanket-add
description: onetest-ai-tm-Elitea's index.json can carry large unrelated local drift; stage the back-write commit with a targeted `git add <case-file-path>`, never `git add -A`, in that sibling clone
type: feedback
---

While back-writing ELITEA-1974's execution status (issue #78), editing one
case markdown file's frontmatter surfaced a ~9,230-line uncommitted local
diff already sitting in `onetest-ai-tm-Elitea/index.json` — unrelated to my
edit, pre-existing, likely a leftover from an earlier untracked
`build_index` MCP call in some prior session (this repo's index can go
stale — see `onetest_mcp_index_can_be_stale.md` — and get silently
regenerated wholesale by a tool call without anyone committing it).

`git status --porcelain` after the edit showed both the case file and
`index.json` as modified. Running a blanket `git add -A && git commit`
here would have swept that whole unrelated regeneration into my
back-write commit — a large, unreviewed, out-of-scope diff riding on a
one-line frontmatter change.

**Rule:** in `onetest-ai-tm-Elitea`, always stage the back-write commit
with `git add <path/to/case-file.md>` — the exact case path, never `-A`
or a directory glob. Leave `index.json` (or any other stray) untouched;
it's out of scope for a back-write and if it needs fixing that's a
separate, deliberate action (rebuild + review), not a side effect of
editing a case's frontmatter. Same instinct as the sync-base-branches
skill's "classify what's there" step, applied to this sibling clone too.
