# Batch Report — pipelines-remaining-w7

## Summary

| Metric | Value |
|---|---|
| Batch | `pipelines-remaining-w7` |
| Base branch | `origin/automation/base` |
| Integration branch | `tests/batch-pipelines-remaining-w7` |
| Cases completed | 11 |
| Outcome | merged-ungated (gate not run) |

---

## Cases

| Case ID | Outcome | Note |
|---|---|---|
| ELITEA-2011 | merged-ungated | gate never produced a verdict (interrupted or dropped) — merged on the trunk but unproven; re-run the gate |
| ELITEA-2070 | merged-ungated | gate never produced a verdict (interrupted or dropped) — merged on the trunk but unproven; re-run the gate |
| ELITEA-2451 | merged-ungated | gate never produced a verdict (interrupted or dropped) — merged on the trunk but unproven; re-run the gate |
| ELITEA-2454 | merged-ungated | gate never produced a verdict (interrupted or dropped) — merged on the trunk but unproven; re-run the gate |
| ELITEA-2443 | merged-ungated | gate never produced a verdict (interrupted or dropped) — merged on the trunk but unproven; re-run the gate |
| ELITEA-2444 | merged-ungated | gate never produced a verdict (interrupted or dropped) — merged on the trunk but unproven; re-run the gate |
| ELITEA-2445 | merged-ungated | gate never produced a verdict (interrupted or dropped) — merged on the trunk but unproven; re-run the gate |
| ELITEA-2446 | merged-ungated | gate never produced a verdict (interrupted or dropped) — merged on the trunk but unproven; re-run the gate |
| ELITEA-2447 | merged-ungated | gate never produced a verdict (interrupted or dropped) — merged on the trunk but unproven; re-run the gate |
| ELITEA-2448 | merged-ungated | gate never produced a verdict (interrupted or dropped) — merged on the trunk but unproven; re-run the gate |
| ELITEA-2449 | merged-ungated | gate never produced a verdict (interrupted or dropped) — merged on the trunk but unproven; re-run the gate |

---

## Findings

### Defects (Product)

- **ELITEA-2011:** PipelineDetailPage.clear_embedded_chat() is a silent no-op (stale locator [aria-label="Clear the chat history"]; real button is chat-clear-button).
- **ELITEA-2070:** Case-text drift — step 6 names a 'status' UI element that doesn't exist as a distinct field in the Run History detail view.
- **ELITEA-2445:** CONFIRMED live, filed as #1381 — a node chained via `transition:` immediately after an `agent`-type node with a nested pipeline never executes; the run still reports 'Completed'.
- **ELITEA-2446:** Code-node script using plain assignment (`output = f"...\"`) does not write state (filed #1383). Flow Editor's 'Add node' clicks do NOT auto-wire edges between sequentially added nodes (filed #1384). Run Details timeline label for Code node reads "pyodide" not the space-stripped YAML id (filed #1385).
- **ELITEA-2454:** Self-filed-then-retracted false-positive #1377 (correctly abandoned after discovering the real mechanism required opening the history toggle first).

### Clarifications (Case-Text Drift)

- **ELITEA-2070:** Step 6 names a 'status' element; status is inferable from response text only, no separate UI field.
- **ELITEA-2451:** Timeline entries appear horizontally left-to-right, not top-to-bottom.
- **ELITEA-2443:** Case uses legacy 'subgraph' nomenclature; the live feature is now the Agent node + pipeline-attach pattern.
- **ELITEA-2445:** Case-snapshot path dispatch issue (no -w7 suffix match).
- **ELITEA-2446:** Case text uses plain assignment (no-op); should use dict-literal or bare name reference.
- **ELITEA-2447:** get_code_node_output_value() returns multi-selected chip text with ZERO separator.
- **ELITEA-2449:** AFS's fixture pre-sets Code node input via YAML, but AFS step 3 instruction to re-select it toggles it OFF (MUI behavior).

### Notes (Process & Intake)

- **All cases:** Case-snapshot path `.agents/automation/pipelines-remaining-w7/cases/<ID>.md` does not exist; actual file path is `.agents/automation/pipelines-remaining/cases/<ID>.md` (no -w7 suffix). Intake dir naming drift.
- **ELITEA-2011:** Sibling ELITEA-2070 in same batch describes related feature (Run History close button). Fixed dead-code defect in page object.
- **ELITEA-2070:** Covering spec additive-only verified (6 removed lines confined to docstring, TestPipelineRunHistoryViewExecutions body untouched). New testid run-history-close-button awaiting human promotion to main.
- **ELITEA-2451:** No pre-existing board #9 issue found; flagged for orchestrator to link/create during Close.
- **ELITEA-2451:** AFS provenance error (non-blocking) — Concrete Handles table claims testids on main; they exist only on automation/testids (added by ELITEA-2450/2452).
- **ELITEA-2454:** New testid pipeline-run-node-history-button added, MUI Menu backdrop-interception gotcha logged to memory.
- **ELITEA-2443:** No pre-existing board #9 issue; no PR-link comment step performed.
- **ELITEA-2444:** Platform-behavior discovery — Run Details Before/After values scoped to selected timeline step, not run-level snapshot.
- **ELITEA-2445:** CONFIRMED CRITICAL — inverted known-defect soft-assertion polarity produced hidden GREEN for open, confirmed, filed defect #1381 (PR #1382, fixed; extended sanctioned_red_soft_assert_traps.md memory entry).
- **ELITEA-2446:** Multiple platform clarifications filed (#1383, #1384, #1385 as questions, not bugs).
- **ELITEA-2447:** Multi-variable input/output return chip text with zero separator; no product defect found.
- **ELITEA-2448:** No product defect; case text is live-correct as written.
- **ELITEA-2449:** No originating board #9 issue found.

### Locator & Framework Compliance

- **All cases:** Mechanical grep for non-testid handles (git diff | grep `get_by_role|get_by_label|get_by_text|…`) returned 0 hits across all diffs. All locators are testid-only.
- **All cases:** No defect masking (no pytest.skip/xit/weakened asserts found).
- **All cases:** Coverage Map rows verified against actual test assertions; all case steps map 1:1.

---

## Gate Verdict

| Metric | Value |
|---|---|
| Verdict | **not-run** |
| Runs completed | 0 |
| Failure count | 0 |
| Duration (s) | — |

The hardening gate was never executed. All 11 cases are merged to the trunk but unproven. **Re-run the gate before promotion.**

---

## Action Items

1. **Orchestrator:** Re-run the hardening gate against `tests/batch-pipelines-remaining-w7` (3 consecutive green runs required per `.agents/testing.md` § Merge gate).
2. **Orchestrator:** Verify case-snapshot path naming for future waves — dispatch prompt uses `-w7` suffix, but actual directory is unsuffixed.
3. **Orchestrator:** Confirm whether per-wave case snapshots should be written during intake or if shared `pipelines-remaining/cases/` is intentional.
4. **Product team:** Review and prioritize the filed defects (issues #1381, #1383, #1384, #1385, #1025 re-encountered).
5. **Testid team:** Promote `run-history-close-button` from `automation/testids` to `main` (human cherry-pick, blocking ELITEA-2070 deployability).
6. **Testid team:** Promote `pipeline-run-node-history-button` from `automation/testids` to `main` (human cherry-pick, blocking ELITEA-2454 deployability).

---

## Archive

All detailed findings, per-case notes, and artifact references are in `report.json`.
