---
name: Board pagination default silently drops recent items
description: gh project item-list without a generous --limit can silently omit the exact card you're looking up, with no error — always pass a limit comfortably above the board's real size when checking one specific card's status
type: feedback
---

## What happened

While auditing #262 (2026-07-20), `env -u GITHUB_TOKEN gh project item-list 9
--owner EliteaAI --format json --limit 200` returned exactly 200 items
(issue numbers 18-563, i.e. the OLDEST 200 by whatever the API's default
ordering is) and did **not** include #262 anywhere in the result — no error,
no truncation warning, just silently absent. The board actually has 564
items; re-running with `--limit 1000` returned all 564 and found #262
immediately (`status: "Ready"`).

## Why this is dangerous

A missing match from a paginated list silently looks identical to "this
card genuinely isn't on the board" — there's no signal distinguishing
"filtered out by the page boundary" from "doesn't exist". For a control
audit specifically, this could have produced a false negative on item 8's
board-status sanity check (or worse, a false "card not found" escalation)
for a delivery that was completely correct.

## Fix

When looking up a **specific card's** board status, always pass a `--limit`
comfortably above the board's actual item count (e.g. `--limit 1000` for
this project's ~564-item board #9), not the tool's suggested/example
`--limit 200`. If the item count is unknown, fetch once with a high limit
and check `len(items)` against what was returned — if it equals the limit,
raise the limit further and re-fetch.

This is a different failure mode from the already-documented
`onetest_mcp_index_can_be_stale` (a source-of-truth staleness issue) — this
is a pure client-side pagination gap on an otherwise-fresh, correct API
response.
