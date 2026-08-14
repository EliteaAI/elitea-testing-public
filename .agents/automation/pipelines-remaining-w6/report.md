# Batch Report — pipelines-remaining-w6

**Summary:** 8 cases processed: 6 automated, 2 already-covered. Gate: **GREEN** (3/3 runs, 179–181s each).

---

## Cases

| ID | Outcome | Note | AFS | PR |
|---|---|---|---|---|
| ELITEA-2043 | automated | Pipeline state panel — attachments module visible/hidden | `l2_pipeline-state-panel-attachments-module_ELITEA-2043.md` | #1365 |
| ELITEA-2044 | automated | Pipeline state panel — delete custom variable | `lextend_pipeline-state-panel-delete-custom-variable_ELITEA-2044.md` | #1366 |
| ELITEA-2066 | automated | Pipeline modules — attachments toggle persistence | `lextend_pipeline-modules-attachments-toggle-persists_ELITEA-2066.md` | #1367 |
| ELITEA-2056 | automated | Pipeline information section — show link modal | `l2_pipeline-information-section_ELITEA-2056.md` | #1369 |
| ELITEA-2064 | automated | Pipeline tools section — attach pipeline as tool | `l2_pipeline-attach-pipeline-as-tool_ELITEA-2064.md` | #1370 |
| ELITEA-2065 | automated | Pipeline tools section — MCP add, view, remove | `l2_pipeline-tools-section-mcp-add-view-remove_ELITEA-2065.md` | #1371 |
| ELITEA-2054 | already-covered | Advanced step-limit persistence (dedup: ELITEA-2021) | `lcovered_pipeline-advanced-step-limit-persist_ELITEA-2054.md` | — |
| ELITEA-2055 | already-covered | Editor notes persistence (dedup: ELITEA-2021) | `lcovered_pipeline-editor-notes-persist_ELITEA-2055.md` | — |

---

## Findings by kind

### Defects (blocking + important)

**ELITEA-2043** — AFS Coverage Map step 7 asserts bidirectional YAML state-section membership (present while Attachments enabled, absent while disabled); implementation Step 6–9 only covered one direction (Step 9 absence only). Fixed: Step 6 now parses YAML while Attachments enabled, Step 9 asserts absence.

**ELITEA-2044** — Priority marker drift: module-level `pytest.mark.p1` is correct for the covering test (ELITEA-2042, high priority) but silently inherited by new sibling test (ELITEA-2044, medium priority). Fixed: added `@pytest.mark.p2` override above the test.

**ELITEA-2056** — Two blocking findings, both fixed:
  1. Raw CSS selector chained off LocatorDescriptor in spec file (`pipeline_page.show_context_diagram_container.locator("svg")`). Replaced with class-level `MERMAID_NODE` constant + page-object methods.
  2. Step 1 had no assertion ("Open pipeline" with no verification it loaded). Fixed: asserts `canvas_wrapper.is_visible()`.

**ELITEA-2065** — Hard-rule violation: `self.page.wait_for_timeout(300)` after hover. Fixed: removed; existing `delete_btn.wait_for(state="visible")` already gates the click.

### Clarifications (case-text drift from live product)

**ELITEA-2043** — YAML `state:` key persists after toggling Attachments off in the same session (doesn't revert to fully absent). Recorded as a durable observation for the next implementer.

**ELITEA-2044** — Case text inconsistency: STATE panel custom-variable delete fires zero network requests (purely client-side) and has no confirmation dialog, unlike other delete flows.

**ELITEA-2056** — Case text either/or: clicking "Show" does NOT navigate (no URL change) but opens a modal with visual Mermaid diagram (satisfies the "visual representation" branch).

**ELITEA-2064** — Case text drift: no "Pipeline sub-tab" exists (same root cause as #530 Agent, #1149 MCP). Also: Save button stays disabled after Tools-section attach because the attach's own PATCH auto-persisted.

**ELITEA-2065** — Same case-text drifts: no MCP sub-tab (#1149), no numeric tools-count display (only toggle to expand list), and removal auto-persists (Save goes disabled).

### Questions (intake/coordination)

**ELITEA-2043, 2064, 2066** — No pre-existing tracker issue on board #9 for these cases. Flagging for the lead to link/create during Close so the PR link + closure record have a home.

### Notes (patterns, precedents, memory)

**ELITEA-2043** — Bidirectional YAML assertion on a panel overlapping the canvas needs close-panel/switch-view/reopen-panel dance at BOTH checkpoints, not just the terminal one. Logged for the next implementer.

**ELITEA-2044** — Discovered pytest gotcha: importing a live UI test function by real name into a tests/unit/ module causes pytest to re-discover and re-execute it (with real browser fixtures) as an import side-effect. Workaround: alias the import.

**ELITEA-2056** — Cross-page testid reuse: `show_context_diagram_container` reuses pre-existing `chat-mermaid-diagram-svg-container` testid (inside shared MermaidDiagramOutput component). Mirrors the pre-existing `copy-id` / `agent-information-section` duplication pattern.

**ELITEA-2065** — Toolkit-card removal mechanics: header-scoped hover targeting + overlay-click bypass via `evaluate()` + removal auto-persists (Save goes disabled). Pattern applies to any future test removing `agent-toolkit-card` on Agent or Pipeline Tools sections (both share ToolCard.jsx).

**ELITEA-2056, 2064** — Testid provenance verified against live EliteaUI git history. All new testids confirmed present on `automation/testids`, awaiting human cherry-pick to `main` per the standard promotability flow.

**ELITEA-2054, 2055** — Already-covered dedups point to the same covering spec (ELITEA-2021, `test_pipeline_create_full_details_persist.py`). Both testids present on `automation/testids`, not yet on `main`. Re-ran the covering spec live as execution evidence (41.94s, green).

**ELITEA-2044** — Dispatch case-snapshot path `.agents/automation/pipelines-remaining-w6/cases/ELITEA-2044.md` does not exist; actual file at `.agents/automation/pipelines-remaining/cases/ELITEA-2044.md` (no `-w6` suffix). 3rd recurrence this campaign. Logged for future intake standardization.

**ELITEA-2064** — Near-miss git hazard: commitlint hook rejected testid commit message, reflexive `git commit --amend` silently amended a stranger's already-pushed commit (ELITEA-2056's) instead of retrying fresh. Caught and repaired via diff inspection.

**ELITEA-2064** — @allure.issue URL link drift: used `ELITEA-2064_attach-pipeline-as-tool.md` but real file is `ELITEA-2064_pipeline-attach-pipeline-as-tool.md`. Fixed; verified link now resolves.

---

## Gate Verdict

| Run | Duration | Status |
|---|---|---|
| 1 | 179.33s | PASS |
| 2 | 178.24s | PASS |
| 3 | 180.80s | PASS |

**Verdict:** GREEN (3/3 consecutive passes, mean 179.4s)

**Branch:** tests/batch-pipelines-remaining-w6  
**Base:** origin/automation/base  
**Failures:** none
