---
name: onetest TMS case IDs can collide across unrelated cases
description: rebuilding index.json for ELITEA-2313 (settings-analytics) surfaced a second, unrelated case also titled ELITEA-2313 under artifacts ("Discard Unsaved Changes")
type: project
---

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
