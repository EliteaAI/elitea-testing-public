---
name: Toolkit detail — Indexes side panel + Test surface on its own route
description: Post-#1616 handles for the toolkit detail view and the Test Toolkit surface
type: project
---

EliteaUI redesign `elitea-testing-public#1616` (live-confirmed 2026-08-27, on
`origin/main`). Indexes has now moved TWICE and the Test surface has left the
detail view entirely.

**Indexes:** standalone tab (`toolkit-detail-indexes-tab`) -> EL-5947 accordion
(`toolkit-indexes-accordion`) -> **side panel** (`toolkit-indexes-panel`,
`IndexesPanel.jsx`, rendered by `ConfigurationTab.jsx`). Both older testids are
absent from `origin/main` AND `origin/automation/testids`.

⚠️ **Use the panel ROOT, not its contents.** On a bare toolkit with no PgVector
connection / Embedding Model configured, `indexingBlocker` is set and the panel
renders only its banner — `toolkit-indexes-count`, `toolkit-indexes-add-button`
and `toolkit-indexes-empty-state` are all **absent at runtime despite existing on
main**. A provenance grep says "on-main ✓" and the handle still never resolves.

**Test surface:** `EditToolkit.jsx`'s tab array now holds exactly ONE entry. The
TEST SETTINGS surface lives at `/toolkits/:tab/:toolkitId/test`, reached via the
detail action-bar `toolkit-test-button` (disabled while the form is dirty; enabled
right after Save). Use `ToolkitDetailPage.open_test_surface()` — it clicks the
product's own button and waits on the URL, never forces the route.
Everything on that surface kept its testids (`toolkit-test-empty-tool-select`,
`toolkit-test-tool-select`, `select-option-{tool_key}`,
`toolkit-test-param-{...}` incl. `recursive`, `toolkit-test-run-tool-button`,
`chat-message-list`). Button LABEL is now "Run Test"; testid unchanged.
`model-selector-button` is NOT rendered here — `LLMModelSelector variant="field"`
early-returns with only `model-selector-name`.
`chat-message-list` does not exist until the first run completes
(`ToolkitTestResults.jsx:29` returns null while `messages` is empty). **That is
absence from the RESULTS column only — do NOT infer the welcome message is gone**
(corrected 2026-08-27, fix round 1 on #1815; the original wording of this note made
exactly that wrong inference). The guidance message was RELOCATED and REWORDED into
the Test Settings column's empty state — `ToolkitTestEmptyState.jsx:29,35`, mounted
at `ToolkitTestPanel.jsx:70`, the same component that carries
`toolkit-test-empty-tool-select`. It carries no testid and has no testid-bearing
container there, so there is no testid-only route to it today: a **live coverage gap
owned by #1857**, not a deleted observable. See
`early_return_null_does_not_mean_the_observable_is_gone.md`.

**Timing:** RUN TOOL is an LLM-mediated conversation turn (posts a conversation +
participant; the tool runs server-side inside it), NOT a REST call. Budget 60s,
not 15s — a 15s wait times out with the assistant message present but empty, which
reads like a broken result and is merely a turn still generating.

Sibling specs still carrying this drift (tracked separately, do not fix in an
ELITEA-1866 PR): `test_github_toolkit.py`, `test_toolkit_parameterized.py`,
`test_credential_usage_in_toolkit_flows.py`.
