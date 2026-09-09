---
name: Run History is a ROUTE, not an inline panel (EL-6537)
description: Since EliteaUI 90e20a03 (2026-09-07) the Run History icon navigates to /…/history; the X close button never mounts.
type: project
aliases: [run history close button, run-history-close-button, EL-6537, RunHistoryContainer onClose, breadcrumb run history]
tags: [area/pipelines, area/agents, type/ui-drift]
created: 2026-09-09
updated: 2026-09-09
---

## What changed

`EliteaAI/EliteaUI@90e20a03` — *feat: [EL-6537] Integrate Agent and Pipeline Run History
into Breadcrumb Navigation* (on `main` 2026-09-07, ancestor of `automation/testids`) —
replaced the inline Run History panel with a dedicated route.

- `src/pages/Pipelines/Components/ConfigurationTab.jsx:359` (and the Agents twin at
  `src/pages/Applications/Components/Applications/ConfigurationTab.jsx:352`) now wire
  `onShowHistory={applicationId ? goToRunHistory : undefined}` → `navigate()` to
  `/pipelines/:tab/:agentId/history` (`src/routes.js:29`).
- That route renders `src/[fsd]/pages/shared/RunHistoryPage.jsx`, which does **not** pass
  `onClose` to `RunHistoryContainer`.
- `RunHistoryContainer.jsx:164` renders the close button only inside `{onClose && …}`, so
  **`run-history-close-button` never mounts anywhere in the app** — the testid string is
  still on `origin/main`, but it is unreachable. No caller in `src/` passes `onClose`.

While Run History is open, `chat-message-input` and `pipeline-history-tab` are **absent**
(different route). The way back is the breadcrumb: `Pipelines / <name> / Run History`,
where link crumbs are `breadcrumb-item` and the last one is `breadcrumb-current`.
`BreadcrumbItem.jsx:30` hardcodes `breadcrumb-item` on the LINK branch and only honours the
route-supplied `testId` on the current branch (`:17`).

## Second trap in the same area

`EliteaAI/EliteaUI@84025881` — *fix: [EL-6391] select the latest run when Run History opens*
(2026-08-26) — auto-selects row 0 on open (`RunHistoryContainer.jsx:93-96`). So row 0 already
carries `data-selected="true"` before any click, and clicking it fires **zero** requests.
Any `expect_response` on `/elitea_core/conversation/prompt_lib/` around a row-0 click is a
race that only passes when the auto-select's own GET lands inside the window. Selecting an
OLDER row (index 1) is still a real click with a real GET — which is why ELITEA-2011 and the
agent-surface `test_agent_run_history_select_past_run` still pass.

Related: [[dev_env_run_harness_and_goto_flake]]
