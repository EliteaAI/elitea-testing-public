---
name: Promotability set is derived from the merged test's call chain, fresh
description: The promotability table's rows come from tracing the merged test's own page-object call chain at check time — never from the AFS table, a prior closure record, or "this PR's new testids"; every dependency is checked against a freshly-fetched origin/main.
type: feedback
---

## Rule

Re-derive the dependency set from code, every time. The AFS both omits real deps
and includes unused ones; a prior record's snapshot ages.

1. `grep -n "^from pages\|Page(page)" <test>.py` → every page object in play.
2. `grep -oE "<var>\.[a-zA-Z_]+" <test>.py | sort -u` → the REAL call chain.
3. Trace each called method/field to its `LocatorDescriptor(testid=…)` or
   UPPER_CASE `[data-testid="…"]` constant. **Include implicit waits** inside
   `navigate()` / `wait_for_page_load()`; skip locator-free helpers.
4. **Diff derived set vs the AFS table BOTH ways.** AFS-listed but never called
   (a documented alternative cleanup path the implementer didn't take) → exclude,
   or you fabricate rows. Called but unlisted → include.
5. **Check every dependency against `origin/main`, not just this PR's new ones.**
   "Pre-existing on `automation/testids`" only means another case put it there;
   it is exactly as un-promoted. Resolve each to its origin commit so the real
   blocking commit gets named. Expect to surface *sibling cases'* gaps.
6. **Cardinality check first** — derived-set size vs table row count. A mismatch
   is the fast tell that a row was dropped, before any SHA tracing. #317's table
   was internally perfect and silently missing 3 genuinely-asserted testids.
7. **Templated families: verify each `LocatorDescriptor`'s LITERAL string
   individually.** A collapsed `toolkit-field-${k}-input` row is fine for
   *presentation*, but the verification behind it must check every literal —
   `toolkit-field-api_key-input-field` (stray `-field`) hid inside a
   mostly-true row and exists nowhere.
8. **Re-anchor to your own fetch.** `origin/main` moves between delivery and
   audit. Re-run both `git merge-base --is-ancestor <dep-commit> origin/main`
   and a content grep against the fresh tree; a record true when written is not
   evidence it is true now.
9. **At 30+ deps, batch:** write all resolved testids to one file and loop the
   grep in a single shell block; one `git log -S` per distinct testid/template
   family (not per row); dedupe commits before citing so "Unblocks when" names
   N distinct commits.

**Sanctioned narrowing (do not apply leniently).** A subset table is not a FAIL
only if ALL hold: every listed row independently verifies correct; the record
explicitly names the sibling issue it inherits from (not bare "pre-existing");
and that sibling's record genuinely carries the full accurate set with SHAs.

## Seen 8×

- #64/ELITEA-1971, #78/ELITEA-1974, #83/ELITEA-1963 — reused `entity-card` blocked on unrelated EliteaUI#544; 2-of-3 correct rows still FAIL. (#544 resolved by #139 — re-check, don't assume.)
- #162/ELITEA-1955 — all 10 listed rows true, one real dep (`agent-toolkit-card`) absent from the table.
- #181/PR#629 — AFS both omitted (`agents-page-header` waits) and over-included (unused UI cleanup path).
- …plus 6 earlier occurrence(s) — full per-case detail in the source entries below.

See also: promotability_must_cover_every_dependency_not_just_this_prs.md ·
promotability_afs_handles_table_can_both_omit_and_overinclude.md ·
promotability_recheck_must_use_audit_time_main_not_delivery_time_main.md ·
full_dependency_promotability_check_surfaces_sibling_case_gaps.md ·
large_dependency_promotability_trace_technique.md ·
templated_promotability_row_can_mask_wrong_literal_testid.md ·
narrower_promotability_table_disclosed_in_sibling_record_not_a_fail.md
