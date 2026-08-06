---
name: gh project rate limit on verification read, not the mutation
description: gh project item-list GraphQL rate-limit error after item-edit means the READ hit the limit, not that the edit failed — retry, don't assume the mutation didn't take
type: feedback
---

Observed 2026-08-06 (issue #871/ELITEA-2363): `gh project item-edit` (moving a
board card status) returned no output — normal, that's success. The
IMMEDIATELY FOLLOWING `gh project item-list ... --format json` verification
read failed with `GraphQL: API rate limit exceeded for user ID <id>`, even
though `gh api rate_limit --jq '.resources.graphql'` showed 68/5000 remaining
at that moment — this is very likely a secondary/abuse rate limit triggered by
rapid successive GraphQL calls (board list + field list + item-edit + item-list
back to back), not the primary quota.

**Don't read this as "the edit didn't take."** It didn't fail — only the
verification read did. Retry the read; don't re-run the mutation, and don't
report the status change as failed/uncertain to the user without retrying
first.

**How to retry:** a `until <gh call>; do sleep 20; done` loop backgrounded via
`run_in_background: true`, polled with `TaskOutput(block:true)` — NOT a
foreground `sleep` (the harness blocks bare `sleep N && ...` outright with
"use Monitor with an until-loop" or backgrounding). Cleared after ~11×20s
(~3.5 min) in this instance with zero further action needed.

Same pattern likely applies to any rapid-fire sequence of `gh project`/`gh issue`
GraphQL calls in one session, not just item-edit specifically.
