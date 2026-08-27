---
name: Settings area backlog (#1398)
description: 128-case settings backlog, wave-by-wave — what's delivered, what's blocked and why, which future waves are queued
type: project
created: 2026-08-26
updated: 2026-08-26
---

## Status after waves w01–w05 (2026-08-28)

**Running total (CORRECTED): 33 `automated`, 12 `merged-sanctioned-red`, 8 blocked, ~75 not yet attempted.**

⚠️ **A sanctioned-RED case is NOT delivered coverage.** `.agents/testing.md` § Merge gate:
it stays `blocked-on-#N` and is never back-written `execution_type: automated`.
On 2026-08-28 I corrected three of my own earlier back-writes that broke this —
ELITEA-2243 (#1771, w01), ELITEA-2289 (#1884, w04), ELITEA-2291 (#1885, w04) —
back to draft/manual + `sanctioned_red: <ticket>`, keeping `automation_test_id` for
CI correlation. Count dropped 36 -> 33. **Re-check prior waves whenever this rule comes up.**

### Wave settings-w05 — `settings/secrets` (14 cases)

4 automated (ELITEA-2345/2346/2348/2349) + 9 `merged-sanctioned-red` (all on OPEN #1203;
ELITEA-2340 also #1903) + 1 blocked (ELITEA-2333 -> #1780). PR #1912.
The workflow's report was wrong twice — cluster A mislabelled `blocked` on a HARNESS
StructuredOutput failure though PR #1902 had merged, and ELITEA-2333/2348/2349 were
**missing from the report entirely** because cluster D's PR #1911 was still open at run end.
Carried #1911 to APPROVED by hand through 3 fix rounds and merged it.
Filed: #1901, #1903, #1909, #1910.

### Wave settings-w04 — `settings/personal-tokens` (11 cases)

8 automated + 2 `merged-sanctioned-red` (ELITEA-2289 → #1884, ELITEA-2291 → #1885) + 1 blocked (ELITEA-2278, attached to #1780 — same case as ELITEA-2250). PR #1900.
**The workflow's gate cascaded `blocked` onto all 11** because its `expected_red[]` was empty; corrected by verifying ground truth then running a node-id-split lead gate (green group 3/3, RED group 3/3 identical). See [[workflow_gate_verdict_is_not_the_merge_gate]].

### Wave settings-w03 — `settings/project-params` (10 cases)

**10/10 automated** (PR #1799) — first clean sweep on this backlog. Lead gate 3/3 green, workflow gate 3/3 green, no red at any point.
Also repaired #1794: the merged ELITEA-2272 spec had been failing every run since the product retired `?view=create` for a real `/edit` route. Filed clarifications #1792/#1793/#1797 (Project Context was redesigned by EL-5888; the case texts describe a single-page layout that no longer exists — AFS assert the live contract per the reverse-masking guard).

### Wave settings-w02 — `settings/notifications` (9 cases)

7 automated (ELITEA-2255/2256/2258/2260/2261/2263/2264, PR #1788, lead gate 3/3 green).
2 blocked → #1789: ELITEA-2265 (no toolkit/credential/vector-store exists to trigger a notification), ELITEA-2262 (all 7 index notifications point at toolkits that now 400).

The lead gate caught a red the workflow's own gate missed; `batch-stabilize` fixed it in one round (timing budget on project 399's 1,049-bucket artifacts list, not the data-selection cause I hypothesised). Suite-health discovery filed as #1790.

### Wave settings-w01 — root `settings` (9 cases)

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
- **4 more sub-areas, ~71 cases**: `ai-configuration` (24), `user-profile` (17),
  `analytics` (15), `users-and-roles` (15).
  (`notifications` w02, `project-params` w03, `personal-tokens` w04, `secrets` w05.)

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
