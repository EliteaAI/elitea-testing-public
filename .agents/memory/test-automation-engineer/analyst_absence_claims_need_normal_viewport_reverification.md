---
name: Analyst absence claims need normal-viewport reverification
description: An analyst's "this element/column doesn't exist" claim (leading to a CLARIFICATION instead of an assertion) can itself be a viewport artifact, not ground truth — reverify at a normal viewport before trusting a live-observation absence claim, and expect it to survive into every section of the AFS that restates it, not just one.
type: feedback
---

## What happened (ELITEA-1808, PR #643, round-2 fix)

The round-1 analyst pass explored the Artifacts file table and concluded "the
file table has exactly four columns (Name/Type/Size/Actions), no visible
upload/last-modified timestamp anywhere in this UI" — filed as CLARIFICATION
#642 (case-text drift, not a defect) rather than asserted, per the
reverse-masking guard. The implementer (me) accepted that premise at face
value and shipped Step 16 without a timestamp assertion.

A round-2 reviewer, then independently the orchestrator, both inspected the
live DOM at a normal 1600×900 viewport and found a real 5th "Last update"
column with a populated timestamp. Root cause: the round-1 analyst's
exploration screenshot had been taken at a narrower viewport that clipped the
column off-screen. It was never actually absent — the reverse-masking guard
was applied to a false negative.

## The generalizable lesson

The reverse-masking guard (`test-automation-workflow` skill, § Hard Rules → 2)
protects against asserting a *stale case-text hypothesis* the live product no
longer matches. But it has a precondition the skill doesn't spell out: the
"live product" observation itself has to be trustworthy. A **narrow-viewport
exploration pass can produce a false "doesn't exist" claim** that looks
identical, in the AFS, to a genuine product-vs-case divergence. Both read as
"CLARIFICATION filed, not asserted" — but one is correct and one is a
tooling artifact.

**Practical guard for future absence claims (implementer AND analyst):**
before filing (or accepting) a CLARIFICATION that something visually
"doesn't exist," reverify at a normal desktop viewport (1600×900 or the
project's stated default) — not the viewport the exploration tool happened
to be running at. A missing column/button/section is cheap to double-check
and expensive to wrongly enshrine as a permanent AFS "NOT asserted" line.

**Full-sweep corollary (same shape as the ELITEA-1839 round-3 lesson):**
once a false absence claim is found in one AFS section, expect it restated
as fact in every other section that touches the same observable. This run,
the same "no timestamp column" claim was baked into FIVE separate spots
(Status bullet, Test Step 16 body + its own sub-bullet, Expected Results,
Coverage Map row, Known Defects Found) — fixing only the two the reviewer
named (Test Step 16 + Coverage Map row) would have left three stale,
internally-contradictory claims in the same document. Grep the AFS for the
claimed-absent element's name/description before calling the fix done.

## Mechanical fix (no new plumbing needed)

If the underlying page-object method already reads the whole row/element as
text (here, `ArtifactsPage.get_file_row_text()` — reads the WHOLE row via
`.text_content()` rather than per-cell locators, because the grid component
has no per-cell testid), a previously "doesn't exist" observable may already
be sitting in the captured string, unasserted. Check before reaching for
`add-data-testid` — the gap is sometimes a missing assertion line, not
missing coverage plumbing. Pattern used here (clock differs per run, so
match shape not value):

```python
LAST_UPDATE_TIMESTAMP_PATTERN = re.compile(r"\d{2}-\d{2}-\d{4}, \d{2}:\d{2} (AM|PM)")
assert LAST_UPDATE_TIMESTAMP_PATTERN.search(row_text), ...
```
