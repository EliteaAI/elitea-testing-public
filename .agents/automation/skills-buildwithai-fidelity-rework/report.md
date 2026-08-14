# Batch Report — skills-buildwithai-fidelity-rework

**Source:** issue #1399 fidelity-audit thread (cross-posted from #1298), human directive
"yes, let's fix affected withing this ticket".

**Batch:** `skills-buildwithai-fidelity-rework` · **Base:** `automation/base` · **Trunk:** `tests/batch-skills-buildwithai-fidelity-rework`

## Summary

| Metric | Value |
|---|---|
| Total cases | 8 |
| Automated | 8 |
| Gate | **GREEN 3/3** (lead-run, independent) |
| Trunk PR | [#1504](https://github.com/EliteaAI/elitea-testing-public/pull/1504) — MERGED (squash) |

## Per-case outcomes

| Case | Unit | Outcome | PR | Notes |
|---|---|---|---|---|
| ELITEA-1989 | TERMINAL | automated | #1501 | rewritten entirely — live generate, response asserted non-empty, review form == response.json() |
| ELITEA-1990 | MIXED | automated | #1502 | pre-populate check → response.json(); edit/create/detail chain (real subject) unchanged |
| ELITEA-1991 | MIXED | automated | #1502 | pre-populate check → response.json(); found+fixed CodeMirror DOM-read test-infra gap (not a product bug) |
| ELITEA-1993 | MIXED | automated | #1502 | Step-1 pre-check → response.json(); validation-rule Steps 2-7 (real subject) unchanged |
| ELITEA-1994 | TRANSIT | automated | #1503 | one-line mock→live swap, no payload assertion existed |
| ELITEA-1995 | TRANSIT | automated | #1503 | same fix (shared parameterized test with 1994) |
| ELITEA-1996 | TRANSIT | automated | #1503 | pre-check name assertion → response.json() |
| ELITEA-1998 | TRANSIT | automated | #1503 | pre-check + negative-check name assertions → response.json() |

## Gate — lead-run, independent

The workflow's own internal gate agent failed twice — first `Connection refused`
(infra), then cut off mid-run after 289s of setup with 0 runs banked. Rather than
retry a third time, the lead ran the gate directly: checked out the trunk, verified
the tree, and ran all 8 node-ids together, 3 SEPARATE invocations
(`.agents/testing.md` § Merge gate):

| Run | Result | Duration |
|---|---|---|
| 1/3 | 8 passed | 214.93s |
| 2/3 | 8 passed | 213.63s |
| 3/3 | 8 passed | 213.39s |

## Landing

Trunk → `automation/base` PR #1504 hit one merge conflict: two append/append
conflicts in daily memory logs (`.agents/memory/qa-engineer/daily/2026-08-14.md`,
`.agents/memory/test-automation-engineer/daily/2026-08-14.md`) against unrelated
work merged to `automation/base` by another concurrent session (ELITEA-2231). Per
the no-edit guardrail, dispatched to `test-automation-engineer` for a union-merge
resolution rather than self-resolved. Verified the target file
(`test_skill_build_with_ai.py`) was byte-identical before/after that conflict
resolution, so the lead's gate (run before the conflict-resolution commit)
remained valid ground truth. PR #1504 squash-merged clean.

## Fidelity + locator + masking greps

Every unit's reviewer ran the mandatory mechanical greps
(`.mock_|page\.route\(|route\.fulfill\(|monkeypatch|\.evaluate\(` for substitution;
new-raw-locator-handle grep; masking-pattern grep) against its diff — **0 hits across
all 3 units, all 3 checks.** Full command + output pasted in each unit's review
findings (see `report.json`).

## Findings worth carrying forward

- **Test-infra fix, not a product defect** (ELITEA-1991/PR #1502): the fabricated
  mock had been masking a live gap — `SkillDetailPage`'s CodeMirror instructions-editor
  DOM read silently truncates long real AI-generated Markdown. Fixed inline by reading
  via `skill_api.get_skill()` (server ground truth) instead of the DOM. No ticket filed
  — this is a test-code fix, not a product bug.
- **Stale AFS Automation Hints** (non-blocking, recorded on 3 units): the merged AFS
  files these tests trace to still carry the fidelity-audit "UNDER REVIEW" banner but
  their own Automation Hints sections further down still recommend the now-retired
  `mock_generate_success()` pattern. Worth a sweep if the #1298/#1399 audit closes out
  AFS files individually.

## TMS back-write

`automation_pr` updated on all 8 case files (`EliteaAI/onetest-ai-tm-Elitea` commit
`9ab2e49`) to point at #1504 — `status`/`execution_type`/`automation_test_id` needed no
change since the rework kept every test's node-id identical.

## Cross-links

Issues #170 (ELITEA-1993) and #139 (ELITEA-1991) — both CLOSED — got a comment noting
the rework landed + PR link. Neither reopened (human's own note: reopening is a human
call).

## Next

None — batch fully landed. 8/8 automated, gate green 3/3, TMS back-written, cross-links
posted. Non-blocking follow-up: the stale-AFS-hints sweep noted above.
