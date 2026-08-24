---
name: Onboarding provisioning state — how to reach it and what the click really does
description: The /onboarding middle state needs the author-details null mock; the Get-Started click starts a 5s poll, not provisioning
type: reference
aliases: [onboarding provisioning, Configuring Personal project, Sure lets go, onboarding-progress-footer, social/author poll]
tags: [area/onboarding, type/live-quirk]
created: 2026-08-24
updated: 2026-08-24
---

## Reaching the provisioning state

`/onboarding` has three states gated on `user.personal_project_id`. The middle one
(tips card + `onboarding-progress-footer`) needs `personal_project_id: null`, which no account in
this environment has. Route-mock `**/social/author/` and null that one field
(`OnboardingPage.mock_fresh_user_state()`, lead ruling `onboarding-w1` DECISIONS § D3) **before
navigating**, then click `onboarding-welcome-get-started-button`.

Always a **fresh browser context**: the click writes `sessionStorage.onboarding_state='true'` and
`showTour` initialises from it (`Onboarding.jsx:36-37`), so a reused context skips the Welcome card.

## The click does NOT provision anything

`handleShowTour()` starts (a) a client-side progress animation (`aria-valuenow` 5, +95/150 per
second, cap 95) and (b) a **5 s poll of `GET /api/v2/social/author/`** (+4.9/+9.9/+14.9 s live).
No provisioning endpoint is ever called — provisioning is backend-side at account creation.
TMS ELITEA-2232 claims otherwise → clarification #1756. Baseline gotcha: `/social/author/` is also
fetched twice during normal page load, so a "nothing polling before" window must start after the
Welcome card is visible.

## Leaving the state

Release the mock → the next poll gets the real `personal_project_id` → footer unmounts,
`WorkspaceIsReady` appears, and **the full app sidebar renders on `/onboarding` itself**
(`MainSidebar` returns null only when `isOnboardingPage && !personal_project_id`).
`sidebar-menu-item-*` fills in progressively (2 items at t+0, all nine by ~3 s) — anchor on one
item with auto-waiting `expect`, never assert the list length.

Related: [[project_briefing]]
