---
name: AFS drift check must sweep the WHOLE document, not just the section a prior round already touched
description: PR #643/ELITEA-1808 ROUND 4 — the exact drift shape round 3 fixed (a summary cell citing a handle the AFS's own body already documents as replaced) recurred in two more sections of the same AFS, present since the original commit, never swept across 3 prior review rounds. Grep the specific fact-strings (not just the section a prior finding named) across the whole file before approving.
type: feedback
---

## What happened

Round 3 of this PR (see `elitea_1808_coverage_map_handle_drift_from_own_test_step_prose.md`)
found and fixed a Coverage Map cell that cited a retired handle
(`bucket-menu-{name}-menu-button` as the Step-7 wait condition) even though
the AFS's own Test Step 7 prose, earlier in the same file, already
documented that handle as broken (hover-gated) and replaced with
`artifacts-bucket-row-{name}`. The round-3 fix (commit `3098bcff`) edited
**only the two Coverage Map cells named in the finding**.

Round 4 (fresh session) re-swept the whole document for the same fact-shape
and found it had **never actually been contained** — it just hadn't been
looked for outside the Coverage Map:

- **Test Step 4** (`test-specs/.../ELITEA-1808.md:133-134`) and
  **Automation Hints point 1** (`:400-405`) both still say the bucket-name
  field is filled via `select-all (Control+a)` + `press_sequentially` — the
  AFS's own Test Data section (`:107-113`) documents this as tried-and-
  rejected ("does NOT select-all on this field... mangled value"), and the
  shipped `ArtifactsPage.fill_bucket_name()` uses `select_text()` +
  `type()`, never `press_sequentially`.
- **Automation Hints point 1** (`:402-404`) also still names
  `bucket-menu-{name}-menu-button` as the Step 6→7 wait condition — the
  exact same retired handle round 3 already fixed in the Coverage Map, just
  in a section round 3 never checked.

Both stale passages have been present since the AFS's **original** commit
(`8207903e`) — they predate every fix round. Round 3's own memory record
even named the generalizable failure mode ("an AFS amendment that touches
only the place the discovery happened, not every place that fact is
restated") but the round-3 session's fix only applied that lesson to the
Coverage Map, not to a fresh grep of the whole file for the same two
fact-strings.

## The generalizable technique

When a review round finds AFS-internal drift (a stale fact restated in one
place while another place already has the correction), the fix is not
"correct the cell/line named in the finding" — it's **grep the specific
claim string(s) across the entire AFS file** before considering the round
closed. Two greps would have caught both remaining instances immediately:

```bash
grep -n "press_sequentially\|Control+a" test-specs/.../ELITEA-1808.md
grep -n "bucket-menu-{name}-menu-button\|CONDITION described in Test Step 7" test-specs/.../ELITEA-1808.md
```

This generalizes `afs_coverage_map_narrow_fix_leaves_sibling_rows_stale.md`
(ELITEA-1839: a fix corrected one Coverage Map row, left 3 sibling rows in
the *same table* stale) one level further — sibling drift isn't confined to
rows in one table, it recurs across *sections* of the same document
(Test Data ↔ Test Step ↔ Coverage Map ↔ Automation Hints all restate the
same handle/technique facts in this AFS format). A fix scoped to "the line
the finding cited" will reliably miss siblings elsewhere in the file.

## Reviewer checklist addition

When re-reviewing a PR with a documented history of AFS drift findings,
don't just re-check the specific cells/lines a prior round's finding named
— re-derive the fact being contested (e.g. "what handle does Step 7 use as
its wait condition") and grep the WHOLE AFS for every restatement of it,
independent of which section a prior finding happened to catch it in.

## Verdict

CHANGES_REQUESTED, round 4. Doc-only fix (same shape as round 3) — zero
functional/test-code risk, 2/2 independent live runs green both times.
Posted: https://github.com/EliteaAI/elitea-testing-public/pull/643#issuecomment-5014729353

## Recurrence — PR #1674 / ELITEA-1970 (2026-08-22, static review)

Test-DATA flavour, not a handle: the implementer hit a real product cap
(Display Name `maxLength=32` silently truncates) and amended § Test Data to a
shorter generated name — but § Test Steps step 1 still spelled out the OLD,
33-char name. The AFS now contradicts itself, and the stale copy is the exact
value known to break, so the next re-point (this case is parked on #1673 to
move back to Github) would copy the broken one. **Check: grep the AFS for the
literal value you just saw amended — an amended constant almost always appears
in two places (§ Test Data and § Test Steps).**
