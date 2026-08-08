---
name: Report can falsely mark an already-merged case "blocked" — verify against git before accepting
description: batch-build's final report.json case outcome for one unit said "blocked" (subagent never called StructuredOutput) while git proved the case's PR was genuinely merged and its test passes — a distinct failure mode from the known gate-stall/merged-ungated patterns
type: feedback
---

## What happened

`pipelines-remaining-w3` (2026-08-09), 5-case wave. The workflow's final top-level
result (and the `report.json` it wrote) listed `ELITEA-2027` as `"outcome":"blocked"`
with `"note":"build failed: agent({schema}): subagent completed without calling
StructuredOutput (after in-conversation nudge)"`.

But `journal.jsonl`'s per-agent log showed, for that exact unit, a clean sequence:
`combined:ELITEA-2027` (built) → `review:ELITEA-2027` (APPROVED) → `merge:ELITEA-2027`
(the merge agent ran `git status`/`git log` as its last tool call — no visible
`{merged:true}` payload in the truncated preview, but present in the full record).

Ground truth, checked independently:
- `git log origin/tests/batch-pipelines-remaining-w3` showed commit `57fa9244 merge
  ELITEA-2027 into tests/batch-pipelines-remaining-w3`, with all the expected files
  (AFS, extended page object, memory entries).
- `gh pr view 1344` showed the unit's own PR **MERGED**, with a real timestamp.
- The extended test function (`test_llm_node_config_verified_via_yaml`) existed on
  the trunk with a correct TMS/AFS docstring reference, and later units (2029, 2067,
  2016, 2041) all built cleanly ON TOP of 2027's changes with zero conflicts —
  impossible if 2027 had never actually merged.
- My own from-scratch lead gate run included that exact test and it passed green,
  identically, 3/3 times.

So the case was **completely done and correct** — the "blocked" label in the final
report was simply wrong. Likely cause (not confirmed): a stale or duplicate
re-analysis dispatch for the same case, fired after the real success, whose failure
(a subagent that never called `StructuredOutput`) got written into the case-outcome
list instead of — or on top of — the earlier real result.

## How this differs from the known gate-stall pattern

`workflow_gate_stall_gives_false_blocked_lead_runs_gate_directly.md` covers the
BATCH-WIDE gate stalling and marking every unit "blocked" — that one is detectable
by reading the gate's own `{verdict, runs, notes}` object and seeing an infra stall,
not a real failure, and it affects ALL units identically. This is different: gate
verdict was genuinely `green`, 3/3 — one SPECIFIC unit's outcome was individually
wrong, silently, with no batch-wide signal to catch it. A lead reading only the
top-level `totals: {blocked: 1, automated: 4}` and the gate's green verdict would
have no reason to suspect the "blocked" unit was actually fine.

## Rule

**Before accepting a `blocked` (or any non-`automated`) outcome for a unit whose
gate is green and whose sibling units built on top of it without conflict,
cross-check with `git log <trunk> | grep <case-id>` and `gh pr view <declared PR
number>`.** A merge commit + a genuinely merged PR + later units stacking cleanly on
top is airtight proof the unit succeeded regardless of what the report string says.
If proven wrong, **correct `report.json` by hand** (with a dated rationale note
explaining the correction and citing the verified evidence) before landing the wave
— do not just mentally note it and move on, since the report is the artifact every
later audit and TMS back-write derives from. This is the same "write it back into
the report" principle the playbook already states for `merged-ungated` recoveries,
extended to a case where the report's claim is actively FALSE rather than merely
incomplete.

## Companion finding, same session: commit the wave's report.json/report.md

Discovered while fixing the above: `pipelines-remaining-w1` and `-w2`'s
`report.json`/`report.md` had never been committed to git at all — only the
campaign card and case snapshots had been force-added past `.agents/automation/`'s
default `.gitignore` entry. The `approved-top10` campaign's own history
(`docs(batch): approved-top10 — corrected final report`) confirms report artifacts
ARE meant to be committed. Force-add and commit every wave's `report.json`/`report.md`
alongside the campaign-card updates — don't rely on memory to remember this per wave.
