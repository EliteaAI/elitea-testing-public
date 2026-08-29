---
name: Settings area backlog (#1398)
description: 128-case settings backlog, wave-by-wave — what's delivered, what's blocked and why, which future waves are queued
type: project
created: 2026-08-26
updated: 2026-08-30
---

## Status after waves w01–w10 (2026-08-30)

**Running total: 83 `automated`, 17 `merged-sanctioned-red`, 13 blocked (human decisions), 15 not yet attempted. NO parked units.**

⚠️ **A sanctioned-RED case is NOT delivered coverage.** `.agents/testing.md` § Merge gate:
it stays `blocked-on-#N` and is never back-written `execution_type: automated`.
On 2026-08-28 I corrected three of my own earlier back-writes that broke this —
ELITEA-2243 (#1771, w01), ELITEA-2289 (#1884, w04), ELITEA-2291 (#1885, w04) —
back to draft/manual + `sanctioned_red: <ticket>`, keeping `automation_test_id` for
CI correlation. Count dropped 36 -> 33. **Re-check prior waves whenever this rule comes up.**

### Wave settings-w10 — `settings/ai-configuration` first half (13 cases)

8 automated (2393/2394/2395/2396/2398/2399/2400/2409) + 3 `merged-sanctioned-red`
(ELITEA-2408 + 2410 -> #1984 required-Name-does-not-gate-Save; ELITEA-2401 -> #1987
Vector Storage card never gets the `Default` badge) + 2 blocked (2417 -> #1982, 2411 -> #1988).
PR #1990. Lead gate: green group 3/3 (248.02/248.21/247.01s, 14 tests); RED group identical 3/3.

**Review caught the write-heavy failure mode I flagged before launch.** In
`test_vector_storage_edit.py`, `default_changed = True` was set *after* the save it guards —
a flake in between would skip the teardown's default-restore while still deleting the
configuration that default pointed at. A spec that passes and leaves damage. Fixed pre-merge.
When a sub-area is write-heavy, say so in the dispatch and the reviewers look for exactly this.

**Harness StructuredOutput false-block, 4th occurrence** (w05, w08, w09, w10) — cluster B
marked `blocked` while PR #1986 was MERGED with all four specs on the trunk. This wave I
corrected `report.json` **before** opening the trunk PR (w09's lesson) and got no add/add
conflict on the way into base. Keep doing it in that order.

**2417 and 2411 are genuine human decisions, not automation gaps.** 2417: a *shared* AI
credential ("ELPS") is visible on every non-public project, so "section hidden when no
credentials" cannot be produced at all. 2411: the case's only observable is false and the
product is internally consistent about it — schema says `"default": null` with no `required`
entry, no asterisk, Save enabled when empty. A contract question, not a defect to assert around.

### Wave settings-w09 — `settings/users-and-roles` (15 cases)

13 automated + 1 `merged-sanctioned-red` (ELITEA-2299 -> #1974) + 1 blocked (ELITEA-2306 -> #1980). PR #1979.
**The most destructive sub-area so far — flagged as such before launch.** ELITEA-2306 REFUSED: testing
"admin cannot delete themselves" requires confirming a self-delete that would destroy the acting
account's only mutable admin membership, with no recovery and no safe proxy. Analyst asked instead of
running it, and did NOT reshape the case into asserting the observed behaviour.
Harness StructuredOutput false-block 3rd occurrence; report.json arrived with NO cases[] at all.
Filed #1970, #1971, #1974, #1975, #1980.

### Wave settings-w08 — `settings/user-profile` (17 cases)

14 automated + 1 `merged-sanctioned-red` (ELITEA-2385 -> #1965, Voice dropdown blank) + 2 blocked (#1960). PR #1969.
**Harness StructuredOutput false-block recurred** (2nd time): cluster D's 4 cases marked `blocked` while PR #1968 was MERGED.
ELITEA-2371 (no consolidated Personalization page — 3 real pages + 1 dead section) and ELITEA-2380
(LONG-TERM MEMORY is dead code, import commented out) both correctly ROUTED, and 2380 deliberately
NOT filed as a bug — an unshipped feature filed as a defect manufactures false red.

### Wave settings-w07 — finished the unit w06 parked (6 cases)

ELITEA-2314..2319 all `automated` (PR #1958, lead gate 3/3 green).
**PR #1945 was found CLOSED** — w06's cleanup deleted its BASE trunk; head branch survived intact.
See [[deleting_a_batch_trunk_auto_closes_open_unit_prs]].
Fix round 3 verified 2 of 3 named blockers were already fixed in round 1 and found a real residual
in each. The explicit "sweep siblings" instruction found 4 more weaknesses. Filed #1959.

### Wave settings-w06 — `settings/analytics` (15 cases)

9 automated (PR #1957). **6 NOT landed — PR #1945 (ELITEA-2314..2319) stays OPEN**: its loop stopped
after 2 fix rounds because the reviewer left surviving blockers UNCLASSIFIED twice, so it could not tell
`unaddressed` from `unfixable`. Blockers are real + specified (Agents-chart data never asserted;
year-boundary arithmetic false-REDs each January; AFS claims KPI assertions the code omits).
**Wave 7 resumes from #1945 — nothing needs re-deriving.**
Cluster A burned rounds on a REPEATING signature (Tools chart, then Agents chart) — a fix round must
SWEEP siblings, not just the named instance.
Also repaired ELITEA-2312's spec (red on base under #1946). Filed #1946, #1947.

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
- **Final wave, 15 cases**: `ai-configuration` second half — ELITEA-2402..2407
  (image/ASR/TTS display + change default), 2412/2413/2414 (persistence after reload),
  2415/2416 (error cases) — plus root cases 2245-2248.
  (`notifications` w02, `project-params` w03, `personal-tokens` w04, `secrets` w05, `analytics` w06.)

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
