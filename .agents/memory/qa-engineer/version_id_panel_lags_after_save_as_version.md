---
name: Information-panel version-id lags the VERSION trigger after Save As Version
description: copy-version-id (Formik) converges ~0.8s AFTER the version trigger (URL-derived) — a one-shot read right after confirm_new_version() is deterministically stale
type: feedback
aliases: [copy-version-id, isFromCreation, confirm_new_version, version id stale, Version ID should change]
tags: [area/agents, area/pipelines, type/race]
created: 2026-08-27
updated: 2026-08-27
---

## The race

On the Agent/Pipeline detail page the VERSION selector trigger and the Information
panel's version-id are fed by **two different sources**:

- `agent-version-selector-trigger` — `ApplicationVersionSelect.jsx`'s `currentVersionId`,
  which starts with `if (isFromCreation) return version;` i.e. it reads the **URL path
  param synchronously**. After Save As Version the app navigates to
  `/agents/all/{agentId}/{newVersionId}?...&isFromCreation=true`, so the trigger flips to
  the new version name **instantly, before any data loads**.
- `copy-version-id` — `ApplicationInformation.jsx` renders `version_details?.id` from
  **Formik**, populated only after the async `GET /version/prompt_lib/{proj}/{app}/{vid}`
  lands and `updateQueryData` writes it.

Measured live (2026-08-27, EliteaUI 0.4.2121): trigger correct at t+0.00s,
`copy-version-id` still the OLD id, converging **0.83s later**.

`AgentDetailPage.confirm_new_version()` waits only on the URL and the trigger text — both
URL-derived — so it returns **inside** that window. A one-shot `get_version_id()` right
after it is deterministically stale (not flaky). Same code, byte-identical, in
`PipelineDetailPage.confirm_new_version()` and (weaker still, no id wait at all)
`SkillDetailPage.save_as_version()`.

## Two traps in that method

1. The first wait — `lastUrlSegment !== prevId` — compares a **version** id against a URL
   whose last segment pre-save is the **agent** id, so it is already true at t=0: a
   guaranteed no-op that guards nothing.
2. `wait_for_network()` = `networkidle`, which this app's persistent Socket.IO polling
   makes unreliable (see `.agents/testing.md` #1847) — and it resolves in the gap between
   the POST finishing and the follow-up GET being issued, so it buys nothing here.

## The right fix

Wait for the **three-way convergence** already proven in
`AgentDetailPage.select_version_by_name()` (`version_id_matches_js`): trigger text ===
name AND `copy-version-id` non-empty AND URL last segment === `copy-version-id`. Hoist
that predicate to a shared constant and use it in `confirm_new_version()` too.

**Never** weaken `assert new_version_id != previous_version_id` — the backend genuinely
creates a new version (verified: 10309 → 10310, `POST 201`, and both ids present in
`GET /agents/{id}`). The product is correct; only the read was early.

Related: [[git_worktree_can_leave_main_checkout_on_wrong_branch]]
