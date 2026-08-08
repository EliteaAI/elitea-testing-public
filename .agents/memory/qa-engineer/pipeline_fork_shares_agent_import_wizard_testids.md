---
name: Pipeline Fork shares the Agent Fork wizard's testids verbatim
description: Fork wizard for Pipelines reuses every agent-* testid from ImportWizardModal; only the menuitem and the completion list's {entityKey} suffix are entity-scoped
type: project
---

Executed ELITEA-2051 (Pipeline — Fork) live, full flow (menu → wizard →
target-project select → confirm → complete → navigate → cleanup), not just
menu-item visibility (ELITEA-2049 only checked the menuitem exists).

**Everything in the Fork wizard is the SAME shared `ImportWizardModal`/
`IWModal*` component tree Agent Fork (ELITEA-1893) already uses — literal
`agent-` prefix is naming tech debt, not entity scoping:**
`agent-import-preview-dialog` / `agent-import-complete-dialog`,
`agent-import-wizard-project-select-combobox`, `select-option-{projectId}`,
`agent-import-preview-name`, `agent-import-preview-card-toggle`,
`agent-fork-confirm-button`, `agent-import-complete-got-it-button` — all
confirmed live for a Pipeline source with zero new testids needed.

**Only two things ARE entity-scoped:**
1. The Fork **menuitem** itself: `pipeline-actions-fork-menuitem` (differs from
   Agent's `agent-actions-fork-menuitem` — `ForkEntityButton.jsx`'s
   `FORK_MENU_ITEM_KEY_BY_ENTITY` map).
2. The completion list: `agent-import-complete-list-{entityKey}` —
   `agent-import-complete-list-pipelines` for a pipeline fork (confirmed live;
   ELITEA-1893's AFS predicted this pattern but never itself confirmed the
   `pipelines` variant — now confirmed).

**Backend classification:** pipelines fork via the SAME `forkAgent`
mutation/endpoint as agents (`POST /elitea_core/fork/prompt_lib/{projectId}`,
body `{main_entity: 'agents', applications: [...]}`) — `IWModalForkButton.jsx`'s
`forkFuncMap` has no separate `pipelines` key; pipelines are backend-classified
as `agents` with `agent_type: 'pipeline'`.

**Pipeline-only addition:** the wizard's Main-entity card additionally shows a
"Pipeline Diagram:" mermaid preview (testid `chat-mermaid-diagram-svg-container`
— genuinely new, no Agent equivalent). It showed "Diagram syntax error
detected" for the specific source pipeline used this session — not filed
(not isolated as a general Fork-preview defect vs that pipeline's own data;
flagged in the AFS for the implementer to re-check with a freshly-created
source).

**Case-text gotcha:** ELITEA-2051's "Forked from link on the dashboard card"
step resolves to the **Pipelines LIST page's card** (`IconLinkWithToolTip.jsx`,
`aria-label="Forked from - Original pipeline"`, no testid, needs-adding —
shared across Agents/Skills/Pipelines list cards), NOT the detail page's
Information-accordion "Forked from:" row (which also exists, separately,
correctly — don't conflate the two when writing assertions).

Full AFS: test-specs/pipelines/l2_pipeline-fork-to-different-project_ELITEA-2051.md
Digest: test-specs/pipelines/_surface.md § Fork wizard
