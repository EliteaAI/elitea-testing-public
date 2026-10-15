---
name: TMS-adjacent issue number can 410 without warning
description: an issue number an AFS/PR cites as "still open" can resolve 410 Gone (deleted) on gh api — not just stale metadata; verify the actual issue, don't trust a carried-over citation
type: feedback
---

## What happened

Reviewing PR #2442 (ELITEA-2310 adjust round 2), the PR body, the test
docstring, and the AFS all cite `elitea-testing-public#1185` as a "still
open, unresolved" prior clarification issue bundling the case-text drift
rows 4/5/6. `env -u GITHUB_TOKEN gh api repos/EliteaAI/elitea-testing-public/issues/1185`
returned `410 Gone` / `"message": "This issue was deleted"` — not 404 (never
existed), not a stale-but-real open/closed issue. `gh issue view 1185` also
fails. A live `gh issue list --state all --limit 500` sweep of the whole repo
confirms issue numbers only go up to ~2446 with gaps — 1185 is in a plausible
range but simply isn't there anymore.

## Why this matters

This citation was NOT introduced by the PR under review — it was carried
over verbatim from the original ELITEA-2310 automation (2026-08, PR #1187),
and the current PR explicitly says "this PR does not touch or resolve that
one." So the drift is pre-existing, not a defect in the diff being reviewed.
But a reviewer who takes "cites an issue number, says open" at face value
without an API check would never catch that the referenced ticket no longer
resolves to anything — the audit trail silently breaks.

## What to do

- When a PR/AFS/test cites a tracker issue as evidence (open or closed),
  hit the tracker API directly (`gh api repos/<owner>/<repo>/issues/<n>`)
  rather than trusting the cited state. Distinguish 404 (never existed —
  likely a wrong repo/number) from 410 (existed, deleted — likely closed as
  duplicate-then-purged, or a repo housekeeping sweep).
- Don't block the PR under review for a citation it didn't create and isn't
  claiming to fix — but DO flag it in the verdict for the orchestrator's
  close-sweep, since the TMS case text update this adjustment hands off to
  the lead will inherit the same dangling reference.
- Not preventive enough to index (narrow, tracker-hygiene lookup) — grep for
  it if a future review hits the same "#NNNN still open" claim pattern.
