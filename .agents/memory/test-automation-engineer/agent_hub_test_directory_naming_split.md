---
name: agent-hub test directory naming split
description: two sibling dirs exist on trunk, tests/ui/agent-hub/ (dash) and tests/ui/agent_hub/ (underscore) — check git log before picking one
type: feedback
---

`automation/tests/ui/` currently has BOTH `agent-hub/` (dash — created by
ELITEA-2366/2367's PR #1429) and `agent_hub/` (underscore — created by
ELITEA-2360's PR #1433, which landed AFTER #1429). Neither has been
consolidated as of 2026-08-11.

When adding a new Agent Hub / Catalog test, check
`git log --oneline -3 -- automation/tests/ui/agent-hub/ automation/tests/ui/agent_hub/`
first and follow whichever directory the MOST RECENT commit touched (top of
that combined log), rather than guessing or picking whichever one sorts
first alphabetically. ELITEA-2361 (2026-08-11) followed `agent_hub/`
(underscore) since ELITEA-2360's test — its own direct predecessor in the
same case family — lives there.

This split is tech debt a future batch should consolidate (pick one, move
the other's file(s), grep for stale imports) — not something any single
case's implementer should silently "fix" by moving files outside their own
diff's scope.
