---
name: Run History is a route now — the X close button never mounts
description: EL-6537 moved Agent/Pipeline Run History to its own route; run-history-close-button is dead, the breadcrumb is the return affordance
type: project
aliases: [run-history-close-button, EL-6537, run history breadcrumb, RunHistoryPage]
tags: [area/pipelines, area/agents]
created: 2026-09-09
updated: 2026-09-09
---

## Fact (verified live on localhost AND dev.elitea.ai, 2026-09-09)

`EliteaAI/EliteaUI@90e20a03` (*feat: [EL-6537] Integrate Agent and Pipeline Run History into
Breadcrumb Navigation*, on `main` 2026-09-07) turned the inline Run History panel into a dedicated
route `/pipelines/:tab/:id/history` (`routes.js:29`), rendered by
`src/[fsd]/pages/shared/RunHistoryPage.jsx` — which passes **no `onClose`**.
`RunHistoryContainer.jsx:164` renders the close button only inside `{onClose && (...)}`, and no
caller in `src/` passes it, so **`run-history-close-button` never mounts at runtime** even though
the testid string still exists in source. Its `LocatorDescriptor` was deleted from
`PipelineDetailPage` (ELITEA-2070 repair, PR #2068).

Return affordance: the breadcrumb trail `Pipelines / <name> / Run History` —
`breadcrumb-item` on every crumb but the last (`BreadcrumbItem.jsx:30`), `breadcrumb-current` on the
last (`:17`). Click the **last `breadcrumb-item`**. Constants on `PipelineDetailPage`:
`BREADCRUMB_ITEM_SELECTOR` / `BREADCRUMB_CURRENT_SELECTOR`.

Opening now NAVIGATES (Configuration form + embedded chat unmount because the route changed), and
returning leaves the embedded chat empty — the live conversation is not restored by back-navigation
(the product offers an explicit *restore conversation* row-menu action instead). Durable claim that
SURVIVED the redesign: the return fires no `conversation(s)/prompt_lib` re-fetch.

`AgentDetailPage` carries the same latent shape and was deliberately left alone (separate card).

Related: [[expect_response_wrapper_races_an_auto_select]]
