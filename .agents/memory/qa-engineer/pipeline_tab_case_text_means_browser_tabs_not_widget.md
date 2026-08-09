---
name: Pipeline "tab" case text means real browser tabs, not an in-app widget
description: ELITEA-2062 reviewer-verified — Pipelines.jsx/EditPipeline.jsx Tabs are nav-only, no multi-open-pipeline tab feature exists
type: feedback
---

When a TMS case for `pipelines` talks about a "tab"/"tablist"/"close button
(X)" that lets several pipelines stay open simultaneously and be switched
between, there is **no such in-app widget** — reviewer-confirmed by grepping
`../EliteaUI/src/pages/Pipelines/*.jsx` for `Tabs`/`role="tab"`: the only
`Tabs` components there are `StickyTabs` (Public/Private view switch on the
list page) and `StyledTabs` (Configuration/other sub-tabs inside a single
open pipeline's edit view) — neither is a multi-document "keep N pipelines
open as tabs" feature. `PipelinesListPage.open_pipeline_by_name()` also has
no `target="_blank"`/`window.open` anywhere under `src/pages/Pipelines` — a
pipeline card click is a plain SPA route push in the SAME document.

The case text's language matches the **browser's own tab strip** instead —
automate via `BrowserContext.new_page()` / `Page.bring_to_front()` /
`Page.close()`, same idiom as
`test_agent_hub_my_liked_reload_cross_tab_sync.py` and now
`test_pipeline_multiple_browser_tabs.py` (ELITEA-2062). If a future
pipelines/agents/skills case reads like a multi-doc-tab UI feature, grep the
relevant page's JSX for `Tabs`/`target="_blank"` first before assuming a
product widget exists — it's very likely describing the browser chrome.
