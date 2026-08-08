---
name: AFS claims need a full-document sweep and a real grep
description: An AFS row, clause, or narrated amendment is a claim to verify mechanically — grep the code for every sub-clause and grep the whole AFS for every stale fact-string. A fix scoped to "the row the finding named" reliably leaves siblings stale.
type: feedback
---

## Rule

Nothing in an AFS is true because it is written down. Two mechanical duties:

1. **Claim → code, per CLAUSE.** For every Coverage Map row, verify each
   sub-observation in the "Asserted where" cell against a real assertion —
   grep the concrete mechanism (`page.on("console"`, the locator, the
   `expect(...)`). A row that exists, names a source and says `asserted`
   proves nothing; a row can honestly assert 2 of 3 clauses and silently
   overclaim the third.
2. **Claim → whole DOCUMENT.** Once a stale fact-string is found (a retired
   handle, an abandoned technique), grep it across the entire AFS before
   closing the round. Test Data ↔ Test Step ↔ Coverage Map ↔ Automation
   Hints all restate the same facts, and a correction made inline during
   exploration rarely propagates to the summary sections.

## Remedy

- Reviewing a fix: never re-check only the named row/cell. Re-derive every
  row of the table from the shipped code, and grep the contested string
  file-wide. A fix instruction phrased *"sweep the whole map/document for
  this pattern"* closes the class in one round; *"fix row X"* reliably
  produces 3–4 rounds of whack-a-mole.
- Audit the DIFF, not the PR narrative: every NEW testid in the EliteaUI
  diff owes a Concrete Handles row plus an update to every Coverage Map row
  whose disposition rested on its absence — independent of what the PR body
  claims to have amended. A mid-implementation defect-find-and-mitigate owes
  a `docs(afs):` amendment in the same PR, exactly like a selector drift.
- Grouped exception claims ("these N non-testid handles are all sanctioned
  by the same carve-out") are per-ROW, never per-paragraph. An `(optional)`
  qualifier does not transfer to neighbours. No qualifier = a live
  `testid needed:` work order. If the same PR added testids to siblings in
  the same component chain, "high blast radius / out of scope" is cost, not
  impossibility.
- A NEGATIVE product claim ("no timestamp column", "the button doesn't
  exist") used to justify a CLARIFICATION instead of an assertion is a
  factual claim about the live system — re-drive the surface yourself at a
  normal viewport. Confirming the CLARIFICATION-vs-bug classification is
  internally consistent is NOT confirming its premise is true.

## Seen 10×

- PR #1294/ELITEA-2464 — Concrete Handles table marked **7 of 9** rows
  `on-main ✓` (`chat-attach-menuitem-button`, `agents-menuitem`,
  `pipelines-menuitem`, `toolkits-menuitem`, `mcps-menuitem`, `toast-alert`,
  and the entire `modules-toggle-{}` family incl. the new `ask_user`) — a
  fresh `git grep -- "<testid>" origin/main -- src/` (per
  `.agents/role-overrides.md` § Analyst slot's mandatory fresh-fetch
  provenance rule) found **zero** matches for all 7 on `origin/main`; they
  exist only on `origin/automation/testids`. Only 3 rows
  (`internal-tools-menuitem`, `toast-message`, `chat-message-input`) were
  genuinely on main. The covering ELITEA-2162 AFS never claimed provenance
  for these 6 handles at all (2464 is the first AFS to touch them) — so
  this wasn't inherited staleness, it was an unverified claim written fresh.
  A `PROVENANCE` column is exactly the same species of claim as a Coverage
  Map "asserted" cell: written down ≠ true, grep it against the actual ref
  before trusting it (and definitely before it feeds a closure record's
  promotability row).
- PR #698/ELITEA-2132 R2 — step-3 row marked `asserted` for 3 clauses; code asserted 2 (never the DOM position the case's own text required).
- PR #693/ELITEA-2095 — row cited "console-error check (Axis 2)"; grep found zero `page.on("console"` in test or page object. Same PR: a page-object method's ambient-data dependency never listed in Test Data.
- PR #639/ELITEA-1839 R2 — round-1 fix corrected the one named breadcrumb row, left 3 siblings identically wrong; R3's whole-map sweep found a 4th.
- PR #1275/ELITEA-2453 — Coverage Map row for case step 8 ("MESSAGES: shows list representation in Before/After") disposed `already-covered-elsewhere`, citing `test_pipeline_run_details_state_before_after.py` (ELITEA-2452) steps 6/8. The cited assertions (`messages_before != messages_after`, `messages_after` non-empty) prove change + non-emptiness but never parse/shape-check the value as a list/array — unlike this SAME PR's own `custom_list` check (step 11: `json.loads` + `isinstance(list)`), which is what "list representation" actually means elsewhere in the identical AFS. The claimed clause ("list representation") was never the one asserted by the covering spec — a cross-spec instance of the same partial-overclaim pattern, not just within-spec.
- PR #1323/ELITEA-2038 — Concrete Handles PROVENANCE row for `agent-add-agent-button`
  claimed `on-main` despite the AFS's own header asserting a fresh `git fetch` +
  dual-ref `git grep` was run. `git log -S'"agent-add-agent-button"' origin/automation/testids`
  found the sole introducing commit (`ce74cd40`, ELITEA-1887) and
  `git merge-base --is-ancestor ce74cd40 origin/main` returned false — the
  testid has never reached `main`. The other 3 rows in the same table
  (`agent-toolkits-section`, `agent-toolkit-card`, `agent-save-button`) were
  correctly `on-main`, so this wasn't a wholesale skip of the check, just one
  stale/wrong row slipping through — same lesson as #1294: verify EVERY row,
  not a sample.
- …plus 5 earlier occurrence(s) — full per-case detail in the source entries below.

See also: afs_amendment_narrates_some_changes_leaves_others_unswept.md ·
afs_coverage_map_narrow_fix_leaves_sibling_rows_stale.md ·
afs_drift_check_the_whole_document_not_just_the_last_fixed_section.md ·
elitea_1808_coverage_map_handle_drift_from_own_test_step_prose.md ·
coverage_map_row_can_partially_overclaim_one_clause.md ·
afs_axis2_claim_needs_grep_not_just_row_presence.md ·
afs_grouped_exception_claims_need_per_row_verification.md ·
elitea_1808_reverse_masking_needs_live_reverification_not_trust.md ·
surface_digest_can_stay_wrong_after_afs_call_site_correction.md (the sweep
extends past the AFS itself — `test-specs/<feature>/_surface.md` is a
SEPARATE file carrying the same class of claim, and it is not one of the
reviewer contract's three named triangulation artifacts, so it drifts silently)
