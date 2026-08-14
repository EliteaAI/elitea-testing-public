---
name: Shared Like.jsx component — testid gap, console error, mutable-data traps
description: Agent Hub / catalog like-unlike surface — shared component testid threading, a filed console-error defect, and two automation traps
type: project
---

`src/components/Like.jsx` (the heart-icon + count control) is a **shared**
component — consumed by `AgentHubLike.jsx` (Agent Hub agent cards), the
data-table widget (`DataTableCell.jsx`/`DataTableRow.jsx`), and pipelines'
`Card.jsx`. Confirmed via source + `git grep`: **zero testids anywhere in the
chain** as of ELITEA-2354 (2026-08-05).

## Testid shape (spec'd, not yet implemented as of this entry)
- Per shared-component discipline, the testid must be a caller-supplied
  `testId` prop threaded from each call site (e.g. `AgentCard.jsx` →
  `catalog-agent-like-button-{application.id}` → `AgentHubLike.jsx` →
  `Like.jsx`), never hardcoded inside `Like.jsx` itself.
- "Liked" state has zero DOM signal difference beyond an icon-component swap
  (`HeartIcon`↔`HeartActiveIcon`, confirmed via screenshot diff) — needs a
  `data-liked="true"/"false"` attribute on the same `IconButton`, same
  precedent as `CategoryRail.jsx`'s chip `data-selected` (ELITEA-2352). Do
  NOT give the two icon states two different testids.
- The like count is a plain text node inside the same `IconButton` — no
  separate testid needed, read via the button testid's `text_content()`.

## Known defect (filed, MINOR, non-blocking)
Every like AND unlike click fires a Redux "non-serializable value in action"
`console.error` — `agentHub/updateApplicationInCategories`'s payload carries
a raw `updateFn` closure (`useAgentHubData.hooks.js:330` dispatches it;
`slices/agentHub.js:42-49`'s reducer invokes it). Dev-console-only noise
(the middleware doesn't run in prod builds); the like/unlike flow itself
(count, icon, backend call, persistence) is entirely correct both directions.
Filed: [EliteaAI/elitea-testing-public#1215](https://github.com/EliteaAI/elitea-testing-public/issues/1215).
**Future analysts on ELITEA-2355 (unlike)/2358 (like from modal)/2364/2365:
expect the same console error and cite #1215 rather than re-discovering it.**

## Two automation traps (not defects)
1. **Like counts are mutable, shared, cross-session product data.** A case's
   named "e.g." example agent will NOT reliably show a specific count
   session-to-session — dynamically discover a card matching the needed
   starting state instead of hardcoding the example name.
2. **The default post-refresh Catalog view only renders the top-6 "Trending"
   cards** (sorted by likes desc) — a freshly-liked LOW-count agent is not
   guaranteed to still render there after a reload. Re-locate via
   `catalog-search-input` instead of assuming the default view.

## Cleanup discipline
Any case that likes an agent MUST unlike it again before ending (verified:
`DELETE /api/v2/social/like/prompt_lib/{project}/application/{id}` → `204`,
mirrors the `POST` → `201` like call) — like state is shared data that
sibling family cases (My Liked filter, reload button, unlike) depend on as a
clean baseline.

Full detail: `test-specs/agent-hub/l3_agent-hub-like-agent-from-list-view_ELITEA-2354.md`
and `test-specs/agent-hub/_surface.md`.
