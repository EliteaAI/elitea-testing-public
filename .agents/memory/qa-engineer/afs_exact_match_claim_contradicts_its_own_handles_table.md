---
name: AFS "confirmed live, exact match" claim can contradict the AFS's OWN Concrete Handles table
description: PR #1269/ELITEA-2450 — AFS Step 8 quoted case-style ALL-CAPS text ("TIMELINE STEP: LLM1", "STATES section header") as "confirmed live, exact match", while the SAME AFS's Concrete Handles table (a few sections later) correctly quotes the JSX source as sentence-case ("Timeline step:", "States"). The narrative section was never corrected to match the table it sits beside.
type: feedback
---

## What happened

`test-specs/pipelines/l3_run-details-open-panel-after-execution_ELITEA-2450.md`
Step 8 (lines 86-88, restated at line 97 and Coverage Map line 113) claims:

> **Expected — confirmed live, exact match**: a "TIMELINE STEP: {node id}"
> line (rendered `TIMELINE STEP: LLM1` ...) ... then a "STATES" section
> header ...

But the same file's Concrete Handles table (lines 135-136), quoting the JSX
source directly, correctly says the wrapped elements are
`"Timeline step:"` Typography and `"States"` Typography — sentence case, no
colon-space-caps rendering anywhere in the actual DOM. The implementer's own
`_surface.md` note (added in the same PR) confirms the live concatenated
text was `"Timeline step:LLM119:03:03"` (no separator, id renders as
`LLM1` not `LLM 1`) — i.e. the table was right, the narrative "exact match"
line was an unexamined echo of the TMS case's ALL-CAPS step wording, never
actually re-verified against what was live.

The implementation (test) correctly asserts the accurate text (matches the
table, matches `_surface.md`) — so no coverage/correctness bug shipped. But
the AFS itself was never amended to fix the narrative/table inconsistency,
which is a standing-check violation on its own (AFS drift discovered during
implementation must get an AFS docs commit in the same PR).

## The generalizable technique

An AFS's Concrete Handles table (which quotes JSX/DOM text literally, as
part of documenting the locator) is a **higher-trust source than the same
AFS's narrative Test Steps / Coverage Map prose** for exact-text claims —
the narrative sections are where an analyst is most likely to unconsciously
echo the TMS case's own stylized wording (ALL CAPS section names, case
formatting) instead of the literal rendered string. When a Test Step says
"confirmed live, exact match" and quotes text, diff that quote against any
later table in the same AFS that also touches the same element — a
same-document contradiction is a free, cheap catch that needs no live
verification of your own; the AFS already contains the disproof.

## Verdict

CHANGES_REQUESTED (single blocking item) — mechanical grep clean, testids
compliant, all clarifications/defects properly filed and referenced,
per-step assertions present; only the AFS Step 8 / Coverage Map wording
needs a same-PR docs fix to match its own Concrete Handles table and the
confirmed-live text.
