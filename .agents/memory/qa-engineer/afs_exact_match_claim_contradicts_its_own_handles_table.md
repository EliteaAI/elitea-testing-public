---
name: AFS "confirmed live, exact match" claim can contradict the AFS's OWN Concrete Handles table — and the drift can live in a companion doc too
description: PR #1269/ELITEA-2450 — ALL-CAPS "TIMELINE STEP"/"STATES" paraphrase shipped as fact in the AFS narrative AND, unfixed by round 1, in _surface.md's "Body composition" bullet — same PR, same drift, different file. Sweep every doc the PR touches, not just the AFS.
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

## Round 1 fix, and what it missed

The fix round amended exactly the 4 spots the blocking finding named
(`l3_run-details-open-panel-after-execution_ELITEA-2450.md` — Step 8
narrative, Expected Final State, Coverage Map row, Concrete Handles cells)
and correctly matched them to the sentence-case source text. It did **not**
touch `test-specs/pipelines/_surface.md`, whose "Run Details panel...
(confirmed live...)" section — added in the SAME original commit as the
AFS — has its own "Body composition" bullet still reading `a "TIMELINE
STEP: {node id}" line ... then a "STATES" section`, i.e. the identical
ALL-CAPS-as-fact drift, unaddressed. Round 2 caught it by re-running the
"grep this quote against every place in the PR that also touches this
element" check against `_surface.md`, not just the AFS file named in the
original finding.

## The generalizable technique, extended

When a fix round's dispatch scopes the blocking item to specific
`file:line`s, that scope is a pointer to where the finding was FIRST
noticed, not a boundary on where the underlying drift lives. A PR that adds
both an AFS and an `_surface.md` digest entry for the same feature in one
commit is very likely to have written the same paraphrase into both — check
every doc-shaped file the PR touches for the same quoted string, not only
the one path the round-1 dispatch named.

## Verdict history

- Round 1: CHANGES_REQUESTED (single blocking item, AFS-file only) —
  mechanical grep clean, testids compliant, all clarifications/defects
  properly filed and referenced, per-step assertions present.
- Round 2 (re-review): AFS file confirmed fixed and internally consistent;
  found the identical drift surviving in `_surface.md`, unaddressed by
  round 1 — CHANGES_REQUESTED again, new item, small mechanical fix.
