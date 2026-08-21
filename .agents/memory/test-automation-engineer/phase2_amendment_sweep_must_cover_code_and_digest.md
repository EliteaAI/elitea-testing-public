---
name: Phase-2 amendment sweep must cover code comments, allure descriptions and the digest
description: Amending only the AFS Test Steps leaves the disproven claim alive in 8+ other places — sweep by keyword across the whole branch diff
type: feedback
aliases: [amendment drift, stale doc claim, doc-sync sweep, allure description over-claim]
tags: [area/handoff, type/process]
created: 2026-08-21
updated: 2026-08-21
---

## What happened

ELITEA-1803/1804/1805 (artifacts landing page). Two mid-build Phase-2
amendments — footer oracle `ArtifactAPI.list_buckets()` → the panel's own
rendered rows, and page-2 named slice → partition because the file table's
default order is **not** name-ascending — were written into the AFS § Test
Steps and nowhere else. Review came back `CHANGES_REQUESTED` on a **docs-only**
blocker: **nine** other places still stated the disproven contract.

## Where the stale claims hide (none of them is the AFS steps)

1. Test module docstring — the per-case "what this covers" bullets.
2. Test module docstring — the § Fidelity paragraph naming the oracle.
3. `@allure.description` — **ships into the report as the test's stated
   contract**, so an over-claim here is externally visible.
4. A module-level constant's comment justifying the test data
   (`PAGINATION_FILE_COUNT`'s "zero-padded because the table sorts by name").
5. The page object's `LocatorDescriptor(description=...)` — the first thing the
   next implementer reads, and it was still telling them to use the racy oracle.
6. `test-specs/<feature>/_surface.md` handle-table row (the later prose section
   was corrected; the table row was not — a self-contradicting digest).
7. AFS § Expected Results (separate from § Test Steps).
8./9. AFS § Coverage Map "Asserted where" column, in **sibling** AFS files that
   share the amended assertion (1803 + 1805 shared the footer oracle).
10. AFS § "stable / read-only" data-strategy section.

## The mechanism that catches it (run at Phase 6, before pushing)

Grep the **disproven claim's keywords** — not the file you amended — across
every file the branch touches, both directions:

```bash
git diff <trunk>...HEAD --name-only | while read f; do [ -f "$f" ] &&
  grep -niE "<old claim keywords>" "$f" | sed "s|^|$f:|"; done
```

Every surviving hit must be either (a) corrected, or (b) an explicit
"this was tried and disproven" amendment note. There is no runtime test for
this class — the sweep IS the regression check.

Related: [[afs_coverage_map_fixes_need_a_full_sweep_not_the_named_row]] ·
[[declared_improvisation_needs_afs_sweep_not_just_pr_narration]] ·
[[afs_is_a_work_order_not_gospel]]
