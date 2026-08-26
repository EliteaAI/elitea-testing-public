---
name: Settings area backlog (#1398)
description: 128-case settings backlog, wave-by-wave — what's delivered, what's blocked and why, which future waves are queued
type: project
created: 2026-08-26
updated: 2026-08-26
---

## Status after wave settings-w01 (2026-08-26)

9 root `settings` cases attempted (the smallest sub-area, chosen as wave 1):

| Case | Outcome |
|---|---|
| ELITEA-2242, 2244, 2251, 2252 | `automated` — merged to `automation/base` via PR #1779 |
| ELITEA-2243 | `merged-sanctioned-red` — tied to open defect #1771, 3/3 identical |
| ELITEA-2249, 2250 | `blocked` — empty-state preconditions unobtainable for the shared `${TEST_USER}` on localhost; needs #1780's decision (provision a project/identity, or rule these manual) |
| ELITEA-2253, 2254 | `blocked` — real logout unobservable on `localhost:5173` (dev-token auth, no Keycloak session); needs #1781's decision (deployed-env CI with an isolated logout-safe user, vs a reduced local spec, vs manual) |

Testids: 6 commits on `EliteaAI/EliteaUI@automation/testids`, not yet on
`main` (human cherry-pick pending) — see the closure record on #1398 for the
full provenance table + SHAs.

## Queued for future waves

- **ELITEA-2245/2246/2247/2248** — role-matrix + unauthenticated-access cases.
  Deliberately NOT grouped into w01: they need multiple identities (admin vs
  viewer/monitor role, an unauthenticated session), a different setup shape
  than the rest of the root `settings` cases.
- **8 more sub-areas, ~115 cases**: `ai-configuration` (24), `analytics` (15),
  `user-profile` (17), `users-and-roles` (15), `secrets` (14),
  `personal-tokens` (11), `project-params` (10), `notifications` (9).

## Pattern for the next wave

1. Pick a sub-area (or a cluster within one) sized 4-12 cases per the
   operator's own steer on this card.
2. Re-check exclusions before carding — a case may have gone `ready` since
   the last sweep (this card has no per-run cap; file/attempt the whole
   qualifying set eventually, not fixed-size forever).
3. Same pipeline: `Workflow` batch-build, lead gate independently, TMS
   back-write, closure record, question issues for anything needing a human
   call — never silently drop a blocked case's follow-up.
4. Card stays `In Progress` until ALL waves land (precedent: #1397, an
   11-case onboarding backlog, closed only at 11/11) — don't move to `Ready`
   after a partial wave.

Related: [[artifacts_area_backlog_1392]] · [[credentials_area_backlog_1394]] (same wave-backlog pattern on other areas)
