# Batch Report — pipelines-remaining-w4

**Summary:** 6 cases processed · 5 automated · 1 already-covered · **GATE VERDICT: GREEN**

---

## Cases

| Case ID | Outcome | Note | PR |
|---------|---------|------|-----|
| ELITEA-2019 | automated | Canvas zoom/pan interaction via ReactFlow | #1351 |
| ELITEA-2057 | automated | Canvas control panel visibility and node-drag methodology | #1352 |
| ELITEA-2060 | already-covered | Covered by ELITEA-2018 (test_pipeline_canvas_delete_node.py) | — |
| ELITEA-2061 | automated | Node auto-increment naming on ADD (title/body drift noted) | #1353 |
| ELITEA-2072 | automated | Left panel collapse button interaction with config persistence | #1354 |
| ELITEA-2048 | automated | Pipeline unsaved-changes and Discard action | #1355 |

---

## Findings by Kind

### Defects (2 blocking findings, both resolved in R1)

**ELITEA-2019 — Missing console-error and network-request assertions**
- Ref: `automation/tests/ui/pipelines/test_pipeline_canvas_zoom_and_pan.py`
- Finding: AFS Axis-2 claimed assertions on zero console errors and zero new network requests at steps 3/5/7. R1 fix: added `capture_console_errors()` and `capture_requests_matching("prompt_lib")` with cumulative assertions now matching AFS exactly.
- Status: fixed

**ELITEA-2019 — Concrete Handles method-name drift**
- Ref: `test-specs/pipelines/l2_pipeline-canvas-zoom-and-pan_ELITEA-2019.md`
- Finding: AFS listed `get_canvas_zoom_scale()` and `get_canvas_pan_offset()` as two separate methods; implementation shipped single `get_canvas_viewport_transform()`. R1 fix: AFS amended to match shipped implementation.
- Status: fixed

**ELITEA-2061 — AFS numeric count mismatch**
- Ref: `test-specs/pipelines/l2_pipeline-node-auto-increment-naming_ELITEA-2061.md:58-68`
- Finding: AFS claimed count == 2/3; implementation asserted 3/4. Root cause: PipelineDetailPage.get_node_count() includes always-present synthetic END node. R1 fix: AFS updated to correct counts with baseline-note explaining END node.
- Status: fixed

### Clarifications (3 documented observations)

**ELITEA-2061 — Case-text title/body drift**
- TMS case title: "Pipeline — Node Duplicate via Node Menu"
- TMS case body: Describes auto-incrementing default node names on ADD
- Finding: No "Duplicate" action exists on pipeline node menu. Case-text mismatch documented in AFS (matches batch convention).

**ELITEA-2048 — Priority marker mismatch**
- AFS declares Priority 'l2 (medium)'; implementation carries @pytest.mark.p1 (matching TMS case's 'high' declaration). Non-blocking cosmetic inconsistency.

**ELITEA-2061 — Case-text example ambiguity**
- AFS Step examples don't correspond to single coherent sequence. Automated the Objective's own internally-consistent example (LLM 1, LLM 2, LLM 3) plus Code type.

### Notes (operational observations)

**ELITEA-2019:**
- Live-confirmed: Synthetic JS PointerEvents via page.evaluate() do nothing on ReactFlow pane (untrusted events). Only real page.mouse or CDP Input.dispatchMouseEvent work correctly.
- Zoom Out clamps at ReactFlow's default minZoom (scale 0.1). Confirmed live but not asserted (out of case scope).
- Pre-existing raw zoom_in()/zoom_out() left as tech debt. New compliant zoom_in_canvas()/zoom_out_canvas() added alongside (additive-only).
- Mechanical raw-handle grep: 5 hits, all compliant (#579 canvas_controls.locator exceptions).
- Coverage Map Axis-1 verified: all 7 case elements map to real assertions.

**ELITEA-2057:**
- Pre-existing zoom_out_canvas() page-object method (added for ELITEA-2019) was never exercised—real previously-silent coverage gap, now closed.
- Methodology trap: dragging via node's MID-BODY on input-heavy nodes silently fails (mouse-down lands on input, not ReactFlow wrapper).
- Latent app-code quirk: FlowEditor.jsx's onReLayout(specifiedExpandAll) does `specifiedExpandAll || expandAll`; on expanded→compact, falls through to stale closure value.
- Additive-only verified: existing test body byte-identical; only module docstring + new test() appended.

**ELITEA-2060:**
- Case phrasing refers to same 3-dot-DotMenu → 'Delete' menuitem flow already automated for ELITEA-2018. Not a distinct control.

**ELITEA-2061:**
- All page-object methods pre-exist and are testid-based (no new locator work).
- App source confirms per-type incrementing-id algorithm.
- Dedup classification sound: closest existing spec adds nodes but renames without asserting auto-assigned names.

**ELITEA-2072:**
- New EliteaUI testid pipeline-config-collapse-button pushed to automation/testids—not yet on main (human cherry-pick gap).
- Self-caught AFS drift (pre-review): "zero network requests" was wrong (expand fires 7 read-only GETs). Narrowed to method="PUT".
- New testid: single static data-testid on IconButton; only child icon swaps. No #277 state-ternary concern.
- Mechanical locator grep: 0 hits (automation/ only). Additive-only verified.

**ELITEA-2048:**
- pipeline_id fixture generates names f"autotest_{request.node.name}"[:32]—lands at field's MAX_NAME_LENGTH=32 cap. Long names trap: 'append suffix' edits silently drop (browser maxlength).
- No new page-object or locator work. Diff touches only test_pipeline_unsaved_changes_and_discard.py.
- New test() appended after existing test (byte-identical). All 8 case steps map to real assertions.

---

## Gate Verdict

**Status:** GREEN

**Runs:** 3 (all passing)

**Durations:**
- Run 1: 227.62s
- Run 2: 224.99s  
- Run 3: 245.38s
- **Median:** 227.62s

**Failures:** None
**Quality flags:** None
**Expected red cases:** None
**Quota halted:** No
**Parked cases:** None

---

## Integration Branch Status

- **Base:** origin/automation/base
- **Integration branch:** tests/batch-pipelines-remaining-w4
- **Artifact files:** .agents/automation/pipelines-remaining-w4/report.json + report.md
- **Status:** Ready for merge & promotion gate
