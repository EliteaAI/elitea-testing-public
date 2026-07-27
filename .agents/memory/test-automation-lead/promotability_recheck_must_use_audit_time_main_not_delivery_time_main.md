---
name: Promotability recheck must use audit-time main, not delivery-time main
description: origin/main keeps moving between a closure record being written and a later control audit reading it — re-derive every dependency commit's on-main status fresh at audit time rather than trusting the record's own git rev-parse snapshot, which is correct-when-written but stale by the time it's audited
type: feedback
---

On the #257/ELITEA-1866 control audit (2026-07-20), the closure record's own
"Promotability verification (fresh, this session)" block pinned
`origin/main` at `84009577...` when it was written. By the time the
independent control audit ran (~4h later), `origin/main` had genuinely
advanced (`68e60d1d..4675190e` — real, unrelated commits landed). A lazy
audit would either (a) trust the record's stated main SHA as still current,
or (b) skip re-fetching because "the record already did this check."

Both are wrong. The correct move (and what this audit did): `git fetch
origin` fresh, then independently re-run BOTH the ancestor check
(`git merge-base --is-ancestor <dep-commit> origin/main`) AND a
bare-substring content grep for the actual testid strings against the fresh
`origin/main` tree — for every dependency commit the record names, not just
the case's own new ones. Only then compare against what the record claimed.

In this instance the re-derivation matched the record exactly (all 14
dependency commits still absent from the now-later `main`, still present on
`automation/testids`) — but that agreement is itself only trustworthy
because it was independently re-derived from current ground truth, not
assumed from the record's timestamp-stale snapshot. A record's promotability
table having been true when written does not make it true when audited;
`main` is a moving target and every control audit must re-anchor to its own
fetch, every time, regardless of how recently the closure record ran the
same check.
