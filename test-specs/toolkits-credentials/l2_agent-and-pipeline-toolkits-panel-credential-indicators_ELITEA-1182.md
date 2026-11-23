# AFS — ELITEA-1182 · Agent and Pipeline Toolkits panel credential indicators

**Status:** ready-for-automation (adjusted 2026-11-23, class A — pipeline flow changed)
**Case:** `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/toolkits_UI/ELITEA-1182_agent-and-pipeline-toolkits-panel-shows-all-three-credential-indicator.md` (33 steps)
**Test:** `tests.ui.toolkits.test_toolkit_indicators_for_credentials.TestPipelineCredentialIndicators.test_pipeline_credential_indicators_e2e` (Agent half, steps 1-11: `TestAgentCredentialIndicators`, unchanged)

## Adjustment (2026-11-23)
- **Triage: class A (UI/flow drift).** Test red at Step 4: `div[data-tour="agent-tools"] button` (the "+ Toolkit" button) no longer exists — the pipeline TOOLS section is a read-only list (EL-7157/EL-7159, `PipelineToolsSection.jsx`); toolkits reach it only through nodes.
- **What changed:** toolkit is added through a Toolkit node (toolkit + tool) and an LLM node (Toolkits multi-select) on the Flow canvas; TOOLS then lists the toolkit with "Used by" chips; the pipeline header shows a warning icon next to VERSION when the saved version has toolkit errors (`VersionSelect.jsx`: aria-label/tooltip `Toolkit(s) configuration issue in <version>`).
- **Validation timing (DEV-verified):** the banner (`credential-warning-banner`) and header icon appear only for the SAVED version after a reload (validate-version runs on load); the test therefore Saves + reloads before checking them.
- **Expected-result changes:** none weakened. Added: Pipeline B (valid credential) checks (steps 26-33), header icon checks (24-25, 33), Used-by chips (17, 29).
- **Declared changes to existing checks:** (1) "click Reload icon, then indicators disappear" → the pipeline card has no Reload icon on DEV, so re-validation after the credential fix is triggered by a page reload; the "indicators disappear / Open in new tab remains" assertions are kept, and the header icon disappearing is added. (2) Open/Reload tooltip texts are now the DEV ones: `Open toolkit in new tab` (was `open in new tab`).
- **Known mismatch (NOT masked):** case steps 20-21 expect a Reload icon + tooltip on the pipeline card. DEV's `PipelineToolCard`/`PipelineToolCardActions` render only Open and Remove (no `#RefreshButton`). Aggregated as a soft failure, so the test is RED until the case text or product is resolved (lead decision: case-text clarification vs product bug).

## Handles Reference (verified on DEV 2026-11-23)
| rung | handle | suggested_testid | provenance |
|---|---|---|---|
| testid | `pipeline-add-node-menu-item-{toolkit|llm}` (via `add_node`) | — | testid on DEV ✓ |
| testid | `pipeline-toolkit-node-toolkit-select`, `…-select-option`, `pipeline-toolkit-node-tool-select` | — | testid on DEV ✓ |
| testid | `pipeline-llm-node-toolkits-select`, `pipeline-llm-node-toolkits-select-option` | — | testid on DEV ✓ |
| testid | `pipeline-tool-card`, `pipeline-tool-card-used-by`, `pipeline-tool-card-open` | — | testid on DEV ✓ |
| testid | `credential-warning-banner` (aria-label = message) | — | testid on DEV ✓ |
| testid | `agent-version-selector-trigger` | — | testid on DEV ✓ |
| label | `Toolkit(s) configuration issue in` (header icon wrapper, aria-label) | `pipeline-version-warning-icon` | ladder — no testid on DEV |
| css | `#RefreshButton` (absence check on pipeline card) | `pipeline-tool-card-reload-button` | ladder — no testid on DEV |
| role | `tooltip` (existing `tooltip` field) | — | existing |
