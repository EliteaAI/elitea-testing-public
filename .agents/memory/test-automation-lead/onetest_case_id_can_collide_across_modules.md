---
name: onetest TMS case IDs can collide across unrelated cases
description: recurred twice now (ELITEA-2313, ELITEA-2320) — a "new" TMS id can already be in use by an unrelated case in a different module; check before trusting the dispatch's named file
type: project
---

## Recurrence #2 (2026-08-05, card #828, ELITEA-2320)

Same pattern again, same day: intake for ELITEA-2320 (settings-analytics,
"Agents tab displays Chat Messages chart…") found a SECOND, unrelated case
file also carrying `id: ELITEA-2320` — `tests/elitea-platform/artifacts/
ELITEA-2320_copy-content-from-three-dot-menu.md` ("Copy Content from
Three-Dot Menu"). Not a fluke from recurrence #1 below — two independent
collisions on the same day means this invariant is actively broken across
the tree, not a one-off drift.

No ambiguity for the dispatch itself: issue #828's body named the exact
source file path, so no guessing was needed to pick the right one. Handled
by working the named file and noting the collision in the closure record
(non-blocking) — did not touch the unrelated artifacts case, did not
rename/dedupe either id.

**Escalate the "For next time" below from spot-check-when-convenient to a
real intake step**: `grep -h '^id: ELITEA-' -r tests/ | sort | uniq -d`
before trusting any single dedup key (filename OR frontmatter `id:`) during
a TMS sweep — two confirmed instances in one day is enough to stop treating
this as rare.

## What happened (2026-08-05, card #821, ELITEA-2313)

While rebuilding `onetest-ai-tm-Elitea/index.json` to pick up the
back-write for `ELITEA-2313` ("Clicking a user row in Users tab opens the
user detail view", `settings-analytics`), the rebuilt index showed **two**
entries with `id: ELITEA-2313` — the settings-analytics one I was working,
and an unrelated `artifacts` case titled "Discard Unsaved Changes"
(`status: draft`, `priority: critical`).

`tms_case_filename_embeds_id_cheap_dedup.md` documents that filenames embed
the id and (as of 2026-07-23) were unique across the tree — this is new
evidence that the invariant can break. A duplicate id is a real hazard for
`correlate_results`/`automation_coverage` (ambiguous match) and for intake
dedup (a "new" card could actually collide with an existing one under a
different module).

## What I did

Nothing — out of scope for this card (single-issue dispatch, `artifacts`
case untouched). Flagged it in the #821 closure record for a human to
triage. Did not silently "fix" the collision (rename an id, delete a case)
without a human decision — that's tracker/TMS content, not something to
guess at.

## For next time

Before trusting `tms_case_filename_embeds_id_cheap_dedup.md`'s
one-id-per-file assumption on a fresh intake sweep, spot-check for
duplicate ids across the full tree (`grep -h '^id: ELITEA-' -r tests/ |
sort | uniq -d`) rather than assuming it still holds from a 2026-07-23
snapshot.
