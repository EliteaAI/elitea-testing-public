---
name: Run History close button has no testid
description: RunHistoryContainer.jsx's close IconButton is aria-label only until a case's own steps click it — requested as run-history-close-button (no surface prefix) by ELITEA-2070.
type: reference
---

`RunHistoryContainer.jsx:77-84` (`../EliteaUI/src/[fsd]/entities/run-history/ui/`) renders the
Run History panel's close (`X`) `IconButton` with `aria-label="close run history"` only — no
`data-testid` on either `main` or `automation/testids` as of 2026-08-09.

- The button IS wired and works (fixes the previously-filed `EliteaAI/elitea-testing-public#1093`
  on both the Agent and Pipeline surfaces — confirmed live on both). It just never got a testid
  because no dispatched case's OWN steps clicked it until ELITEA-2070 ("Pipeline — Run History
  Panel", which explicitly lists "close run history panel" as a numbered step).
- ELITEA-2011 (Pipeline) and ELITEA-1877 (Agent) both explored this panel deeply but neither
  case's text asked to close it — per locator-policy scope discipline (testids only where a
  case's steps actually touch an element), neither requested the testid. This is NOT an oversight
  to "fix" retroactively in those specs; it's the policy working as intended.
- Naming: requested `run-history-close-button` — **no `pipeline-`/`agent-` prefix** — because
  `RunHistoryContainer` is a shared entity (`src/[fsd]/entities/run-history/`) serving both
  surfaces with the literal same `IconButton`, same reasoning already established for
  `run-history-list-item` (also prefix-less).
- If you're implementing/reviewing ELITEA-2070 (or any future case that closes this panel): the
  testid request lives in
  `test-specs/pipelines/lextend_pipeline-run-history-panel-close_ELITEA-2070.md`. Don't add a
  `close_run_history()` method to `AgentDetailPage` unless an Agent-surface case actually
  dispatches and calls it — the Agent page object's own comment ("no close locator/method exists
  on purpose") stays accurate until that happens, even though the underlying component/testid is
  now shared-ready.
