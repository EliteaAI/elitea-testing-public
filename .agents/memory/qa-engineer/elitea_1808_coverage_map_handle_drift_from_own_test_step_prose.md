---
name: ELITEA-1808 Coverage Map handle drift from the AFS's own Test Step prose
description: PR #643 round 3 — a Coverage Map "Asserted where" cell cited a wait-condition handle the AFS's own Test Step section (same file, earlier) explicitly documents as broken and replaced; the correction propagated to the prose but not to the summary table. Check the Coverage Map against the AFS's OWN body, not just against the shipped code.
type: feedback
---

## What happened

PR #643 / ELITEA-1808, round 3 (fresh session, rounds 1-2 not inherited).
Round 2 had already fixed a *factual* AFS error (false "no timestamp
column" premise — see `elitea_1808_reverse_masking_needs_live_reverification_not_trust.md`)
and swept it across the file. Round 3 found a *different* kind of AFS
self-inconsistency that survived both rounds 1-2: the Coverage Map's
Step 7 row (`test-specs/artifacts/l2_..._ELITEA-1808.md:256`) says:

> dynamic `bucket-menu-{name}-menu-button` becomes visible

But the AFS's own **Test Step 7** body — same file, ~100 lines earlier —
explicitly documents that this exact handle does NOT work as a wait
condition (it's hover-gated, `display:none` until the row is hovered,
never reaches Playwright's "visible" state on an unhovered row) and that
the implementer switched to `artifacts-bucket-row-{name}` instead. The
shipped code (`ArtifactsPage.wait_for_bucket_in_list()`,
`artifacts_page.py:495`) uses `BUCKET_ROW` (`artifacts-bucket-row-{}`),
confirming the Test Step 7 prose is right and the Coverage Map cell is
stale.

Also found (Nit, not blocking): Step 8's cell claims "menu with 4 items
visible after hover+click" — the shipped test only asserts 1 item
(`bucket_menu_upload_files_menuitem.is_visible()`), the other 3 are
explicitly out-of-scope per the AFS's own documented scope ruling (no
testid added). Not a coverage gap (the case's own "dropdown appears"
requirement is satisfied by 1 item's visibility) — just table wording
overselling relative to code.

## The generalizable technique

This is a *sibling* failure mode to `afs_coverage_map_narrow_fix_leaves_sibling_rows_stale.md`
(ELITEA-1839, where a fix corrected one Coverage Map row but left the
identical inaccuracy in 3 sibling rows of the *same table*). Here the
drift is across *different sections of the same document* — a Test Step
paragraph got amended (correctly) when the implementer discovered the
handle didn't work live, but the Coverage Map summary table one section
later, which restates the same fact in compressed form, never got the
matching edit. Two distinct sweep failure shapes, same root behavior:
**an AFS amendment that touches only the place the discovery happened,
not every place that fact is restated.**

Reviewer technique going forward: when ticking the Coverage Map's
"Asserted where" column, don't just check it against the shipped code —
also check it against the AFS's OWN Test Step section for the same step.
A Test Step body and its Coverage Map row should tell the same story;
when they diverge, one of them is the stale one (usually the summary
table, since Test Step corrections tend to happen inline during
exploration/implementation and the Coverage Map is often written first
or edited last as a wrap-up pass).

## Verdict

CHANGES_REQUESTED — both findings are AFS-doc-only (zero functional
risk, zero test-code change), a quick table-cell edit closes the round.
Everything else (2/2 independent live-green runs, POM discipline,
additive-only, no defect masking, the round-2 timestamp regex verified
meaningful against a real captured `row_text`, Correction record honesty
cross-checked against the PR thread and issue #642's live state) was
clean. Posted:
https://github.com/EliteaAI/elitea-testing-public/pull/643#issuecomment-5014668655
