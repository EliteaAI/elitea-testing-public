---
name: onetest MCP index can be stale — build_index before trusting a "not found"
description: mcp__onetest-tms__get_test_case can return "not found" for a case that genuinely exists on disk if index.json hasn't been rebuilt since the case was added; run build_index before concluding a case ID is wrong or the case is missing
type: feedback
---

Hit on ELITEA-1889 (issue #67): `get_test_case(id="ELITEA-1889")` returned
`not found: ELITEA-1889` even though the source markdown file existed at
the expected path in `onetest-ai-tm-Elitea` with `id: ELITEA-1889` in its
frontmatter — an exact match. `search_test_cases` also came back empty for
the same case. Running `mcp__onetest-tms__build_index` (2226 cases
indexed) fixed it immediately — `get_test_case` then returned the full
markdown on the very next call.

**Why this matters:** the failure mode looks exactly like "this case ID is
wrong" or "the case was never actually filed," which invites either
re-deriving the ID from the file path (fragile, error-prone) or wrongly
concluding the case doesn't exist / escalating a non-problem. The actual
cause is index staleness — the MCP server's `index.json` is a cached
artifact, not a live query over the repo, and nothing in this project's
tooling auto-rebuilds it when new case files land in the sibling clone.

**Fix:** if `get_test_case` or `search_test_cases` returns empty/not-found
for an ID you can see with your own eyes in a file (`id:` frontmatter
matches exactly), run `build_index` once and retry before treating it as a
real gap. Cheap, idempotent, safe to run defensively at the start of any
analyst dispatch that will fetch via this adapter.
