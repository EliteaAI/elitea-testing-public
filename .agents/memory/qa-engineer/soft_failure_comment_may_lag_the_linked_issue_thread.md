---
name: A soft-failure's inline comment can lag its own linked issue thread
description: Cross-check a "Known defect #N" comment's causal claim against #N's own comment thread, not just the issue body — the claim may be stale
type: feedback
---

## What happened (ELITEA-2033, PR #1145, reviewer slot)

`test_pipeline_router_node_configuration.py`'s Step 9 wraps the post-reload
default-output-edge check in the standard `soft_failures` pattern, with a
comment claiming: "since default_output was never actually written
client-side, it was never persisted by Save either, so the edge cannot
survive a reload (the app's YAML->canvas parser only draws this edge when
default_output is truthy)."

That claim is **factually wrong**, and the PR's own evidence proves it: a
prior comment on the linked issue (`elitea-testing-public#1036`, posted
2026-07-24 during an earlier abandoned attempt) source-verified that
`parsePipeline.helpers.js`'s parser synthesizes the **identical** edge id
whether `default_output` is truthy or falsy/empty — the edge is a
display-only convention, not proof of persistence. The CURRENT implementer's
own follow-up comment on the same issue (2026-08-04) even reports "the
post-Save-and-reload edge check passed cleanly in both runs" — directly
contradicting the in-code comment written in the same PR.

Net effect: the Step 9 assertion is not wrong per se (it checks something
real — the edge testid is present) and doesn't cause a false green/red, but
it can **never** distinguish "defect #1036 fixed" from "defect #1036 still
broken" — it will pass unconditionally either way — while its comment claims
the opposite (that it proves persistence). This is not classic masking (the
real defect IS caught, at Step 6's pre-Save edge check), but it is a
misleading self-documentation trap: a future reader debugging #1036 or
reasoning about coverage would trust the wrong causal story.

## What to do as reviewer

When a test's inline comment attributes a "known defect" causal mechanism —
especially for a check wrapped in `soft_failures`/`try-except` — **read the
linked issue's full comment thread**, not just the issue body. A corroborating
comment posted during the SAME implementation session (or an earlier
abandoned attempt) may already contain a correction that never made it back
into the test file's comment. Ask: "does this assertion's plain-language
justification match what's actually verified, or could it pass regardless of
the defect's state?" — if the latter, flag it even though the test doesn't
mis-report a result.

## Where seen

ELITEA-2033 / PR #1145, `automation/tests/ui/pipelines/test_pipeline_router_node_configuration.py`
Step 9, cross-referenced against `elitea-testing-public#1036` comment thread.
