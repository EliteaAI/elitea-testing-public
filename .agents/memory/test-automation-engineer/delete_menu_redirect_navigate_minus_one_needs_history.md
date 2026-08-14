---
name: Delete-via-menu redirect uses navigate(-1) — needs real browser history
description: Pipeline/Agent delete-via-menu redirect is history.back(); page.goto()-reached detail pages never redirect (#1332)
type: feedback
---

## What

EliteaUI's shared `useDeleteApplication` hook
(`src/pages/Applications/Components/Applications/DeleteApplicationButton.jsx`,
covers BOTH Agent and Pipeline entities via `isFromPipeline`) wires the
post-delete redirect to the success toast's close event:

```js
const onCloseToast = useCallback(() => {
  if (isSuccess) {
    setBlockNav(false);
    setTimeout(() => { navigate(-1); }, 0);
  }
}, [...]);
```

`navigate(-1)` is React Router's `history.back()`. If the detail page was
reached via a direct navigation (`page.goto()` — e.g. `PipelineDetailPage.navigate(pid)`
/ `AgentDetailPage.navigate(id)`, the standard pattern after
`pipeline_api.create_pipeline()` / `agent_api.create_agent()`), there is
**no prior in-app history entry** to go back to. `navigate(-1)` is then a
silent no-op — the app stays on the deleted entity's stale detail route
indefinitely. No console errors, no visible error state. Confirmed live via
Playwright MCP: 8s poll, DELETE returns 204 (entity genuinely gone
server-side), URL never changes.

Filed: `EliteaAI/elitea-testing-public#1332` (Pipeline case; same code path
likely affects Agent delete-via-menu too — not separately verified).

## What this changes about your first move

Before writing/extending ANY "delete via three-dot menu, verify redirect to
dashboard" assertion for Agents or Pipelines: **check how the test reaches
the detail page.** If it's `detail_page.navigate(id)` (direct goto, the
standard/established pattern in this suite), the redirect assertion WILL
fail deterministically — that's not a test bug, it's `#1332`. Use the
`soft_failures` + `# Known defect: #1332` pattern (see
`test_pipeline_management.py::TestDeletePipeline::test_delete_pipeline_via_ui_menu`,
ELITEA-2022), and still reach the dashboard explicitly (`list_page.navigate()`)
for any downstream "entity absent from list" assertion so it isn't masked by
the known defect.

If a future test reaches the detail page by clicking through from the
dashboard (real SPA navigation, real history entry), the redirect DOES work —
don't blanket-disable the assertion; the failure is reachability-dependent.
