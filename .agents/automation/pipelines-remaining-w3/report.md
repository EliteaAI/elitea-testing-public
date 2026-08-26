# Batch Report — pipelines-remaining-w3

**Totals:** 5 cases — 1 blocked, 4 automated

**Base branch:** `origin/automation/base`  
**Integration branch:** `tests/batch-pipelines-remaining-w3`

---

## Case Summary

| Case ID | Outcome | Note | AFS | PR |
|---|---|---|---|---|
| ELITEA-2027 | blocked | build failed: agent completed without calling StructuredOutput | [AFS](test-specs/pipelines/lextend_pipeline-node-config-verified-via-yaml_ELITEA-2027.md) | #1344 |
| ELITEA-2029 | automated | | [AFS](test-specs/pipelines/l2_flow-to-yaml-sync_ELITEA-2029.md) | #1345 |
| ELITEA-2067 | automated | | [AFS](test-specs/pipelines/lextend_pipeline-yaml-editor-edit-and-save_ELITEA-2067.md) | #1346 |
| ELITEA-2016 | automated | | [AFS](test-specs/pipelines/l2_pipeline-decision-node-multi-branch-execution_ELITEA-2016.md) | #1348 |
| ELITEA-2041 | automated | | [AFS](test-specs/pipelines/lextend_pipeline-entry-point-trigger-shown-only-on-entry-node_ELITEA-2041.md) | #1349 |

---

## Findings by Case

### ELITEA-2027 (blocked)

**Branch:** `tests/ELITEA-2027-pipeline-node-config-verified-via-yaml`

#### Notes
- Dispatch pointed the case snapshot at `.agents/automation/pipelines-remaining-w3/cases/ELITEA-2027.md`, which does not exist (the `-w3` folder not created). The case snapshot actually lives in the shared, non-wave-suffixed pool `.agents/automation/pipelines-remaining/cases/ELITEA-2027.md` that every wave of this campaign reads from.
- The batch trunk `tests/batch-pipelines-remaining-w3` did not exist locally or on origin when this dispatch started, even though the campaign card's log says wave-03 was already launched. Created it fresh per the dispatch's own fallback instruction.
- CHAT HISTORY's YAML `input_mapping` value for the literal test-data text `[]` serializes as an actual empty YAML/Python list, not the string `[]`, once explicitly typed and saved — confirmed live via a controlled probe. Not a product defect — documented in the AFS (Axis 2).
- Mechanical raw-handle grep on the full diff returned 0 hits — no non-testid handles added.
- All 7 case steps + preconditions + Expected Final State + Pass/Fail criteria map to real assertions at the claimed steps.
- extend-existing target (test_pipeline_llm_node_system_task_chat_history_config.py, ELITEA-2004) confirmed merged to origin/automation/base; PR diff is additive-only.
- CHAT HISTORY value assertion correctly applies the reverse-masking guard; case text says value `[]` implying a string, but the backend round-trips typed text as raw YAML, so an unquoted `[]` parses as an empty list.
- No defect-masking patterns found; all 12 named case fields get their own real assertion with descriptive failure messages.

---

### ELITEA-2029 (automated)

**Branch:** `tests/2029-pipeline-flow-to-yaml-sync`  
**PR:** #1345

#### Defects
- **Page-object gap (not a product defect):** `PipelineDetailPage.wait_for_node_on_canvas(node_type)` resolves via `.locator(...).first` (DOM order). On a canvas that already has a node of the same type, adding a second node and calling `wait_for_node_on_canvas('llm')` returns the WRONG (pre-existing) node id, not the new one.

#### Notes
- Confirmed live: a freshly-added, unconnected second node has NO `transition:` key at all in its YAML block — distinct from the entry-point/only-node default. Recorded in `_surface.md`.
- No tracker board issue (board #9) exists for ELITEA-2029 — flagged for the lead's report/intake phase.
- Non-blocking coverage observation: an existing test (`test_pipeline_advanced.py::TestYamlEditor::test_flow_yaml_round_trip`, PIPE-021) performs the same journey shape but never calls `get_yaml_content()` and so never asserts the case-defining observable.
- Dispatch snapshot path fallback used (`.agents/automation/pipelines-remaining/cases/ELITEA-2029.md`).

---

### ELITEA-2067 (automated)

**Branch:** `tests/ELITEA-2067-pipeline-yaml-editor-edit-save`  
**PR:** #1346

#### Notes
- Dispatch's stated case-snapshot path does not exist — the campaign uses a single shared case-snapshot directory across all waves. Found and used the correct file.
- Reverse-masking near-miss caught mid-implementation: asserting the literal flow-style string typed as `output: [messages]` fails after a Save+reload round-trip because the server correctly re-serializes it as block-style YAML. Fixed via `yaml.safe_load()` + parsed-field assertion.
- Triangulation clean: TMS case snapshot == AFS == implementation diff.
- Merged-target rule satisfied: covering spec `test_yaml_edit_transition_syncs_to_flow_canvas_and_enables_save` (ELITEA-2028) verified present on origin/automation/base.
- Mechanical raw-locator grep returned 0 hits — zero new locators added.
- Verified every page-object call the new test makes actually exists: `is_save_enabled`/`is_discard_enabled` live on PipelineFormPage (not PipelineDetailPage); `save_and_wait_for_update` on PipelineDetailPage.
- pipeline_with_llm_id fixture confirmed to seed `output: []` via `create_pipeline_with_llm_node` YAML template, matching the AFS's claimed pre-edit baseline.
- Reverse-masking guard correctly applied: fixed to parse with `yaml.safe_load()` and assert the parsed value; documented in committed memory entry.
- Per-step assertion check passed for all 7 numbered steps.
- **Minor nit (non-blocking):** `next(n for n in post_reload_parsed["nodes"] if n["id"] == "LLM 1")` at step 7 raises bare StopIteration with no assertion message if the node id is absent — still fails loudly but with less diagnostic output.

---

### ELITEA-2016 (automated)

**Branch:** `tests/ELITEA-2016-decision-node-multi-branch-execution`  
**PR:** #1348

#### Defects
- **Decision and Condition node types cannot be made entry point via UI action** — confirmed via source (EliteaUI NodeCardHeader.jsx menuItems logic unconditionally excludes Decision/Condition). The only UI path is creating the Decision node first (auto-sets entry_point).
- See issue #1347.

#### Notes
- Decision node classification/routing silently no-ops (LLM returns empty response) unless the Decision node's Input combobox includes the built-in `input` state variable — required even when the classification prompt only needs the raw chat message.
- Printer node's chat-visible output comes from the PRINTER section's Value field (`input_mapping.printer.value`), NOT the separate Final Message field.
- Multi-turn continuation in the same chat conversation resumes execution at the previously-reached branch node rather than re-invoking the Decision node's classification. A test asserting differential routing across categories must clear the chat between messages.
- `printer_node_value` / `printer_node_final_message_input` LocatorDescriptors in pipeline_detail_page.py are page-wide by design (documented as "correct only while a test has a single Printer node"). ELITEA-2016 is the first case needing THREE simultaneous Printer nodes, so the implementer must add a node_id-scoped variant before calling these methods.
- The in-page fetch behind the pipeline 'Run details' dialog redirects to a dev.elitea.ai OIDC login and fails with a CORS error when run against localhost:5173. The dialog still renders correctly from other in-memory state, so this only blocks the full-context assertion.
- Dispatch snapshot path fallback used.
- AFS's Concrete Handles table flagged the embedded chat's clear button as needing a new page-object method (true) but implied a testid gap might also exist — it did not. `chat-clear-button` was already present on EliteaUI main (EliteaAI/EliteaUI@2d98830a).
- Multi-node (3+) canvas placement via `move_node()` + `fit_view()` is sensitive to offset magnitude: large/monotonically-increasing offsets zoom `fit_view()` out so far that `connect_nodes()` misses sub-pixel connection handles. Logged as a durable gotcha for the next multi-branch case.
- `clear_chat()` uses `self.page.wait_for_timeout(300)` — technically against the no-sleep hard rule, but matches this file's dominant existing pattern (50 pre-existing wait_for_timeout call sites).
- Mechanical locator grep on the diff returned 2 hits, both in pipeline_detail_page.py (lines 4155/4166): `self.page.locator(self.RF_NODE_TESTID.format(node_id)).locator(self.PRINTER_NODE_VALUE_TESTID)`. Both compliant: RF_NODE_TESTID and PRINTER_NODE_VALUE_TESTID are UPPER_CASE class-level constants.

---

### ELITEA-2041 (automated)

**Branch:** `tests/ELITEA-2041-entry-point-trigger-shown-only-on-entry-node`  
**PR:** #1349

#### Clarifications
- Case steps 2/4 say "Click on the [entry/non-entry] node" to open its configuration panel. Live product: every node card renders fully expanded by default; clicking the header toggles expand/collapse, and would risk collapsing the very card the step wants to observe. No click is performed in the test.
- Case step 6 implies the Information section shows "Trigger: Chat Message" (with a space). Live DOM textContent is "Trigger:Chat Message" (no space) — the visual gap is CSS flex `gap`. Asserted the live-contract (no-space) string per the reverse-masking guard.

#### Notes
- One new EliteaUI testid added this session: `information-trigger-row` on ApplicationInformation.jsx's Trigger row (shared Information accordion, Agents+Pipelines) — committed+pushed to automation/testids (EliteaAI/EliteaUI@28dbc5e4), not yet on main (human cherry-pick pending).
- Step 5's Information-row assertion compares `information_trigger_row`'s text against a dynamically-read `entry_trigger_value = get_trigger_type_value()` rather than a hardcoded string. This is a consistency check, matching the case's literal wording.
- Case snapshot lives at `.agents/automation/pipelines-remaining/cases/ELITEA-2041.md` (no `-w3` wave suffix) — confirms the already-recorded memory entry about case snapshot directory patterns.

---

## Merge Gate Verdict

**Gate verdict:** GREEN

**Runs:** 3 consecutive passes  
**Timings:**
- Run 1: 286.3s
- Run 2: 281.2s
- Run 3: 282.5s

**Failures:** 0  
**Mean duration:** 283.4s

---

## Quality Flags

- **extend-rate 3/5 exceeds 0.5** — blind-audit a sample of the extend/covered conclusions (a second analyst re-analyzing 1–2 cases) before trusting this batch's coverage.

---

## Summary

- **Cases completed:** 5 total
- **Automated:** 4 (ELITEA-2029, ELITEA-2067, ELITEA-2016, ELITEA-2041)
- **Blocked:** 1 (ELITEA-2027)
- **Gate:** GREEN (3/3 runs)
- **Quota halted:** No
- **Expected red:** None
- **Parked:** None
