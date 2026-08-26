---
name: Onboarding tour+banner state needs no mock — and arms a blocking tour prompt on the next page
description: /onboarding as an ordinary user lands straight in the tour+ready state; it also arms a modal tour prompt that blocks the next page
type: reference
aliases: [onboarding tour, jump in now, first visit prompt, interactive tour prompt, onboarding tips card]
tags: [area/onboarding, type/quirk]
created: 2026-08-24
updated: 2026-08-24
---

## The state machine (verified live 2026-08-24, localhost:5173)

`Onboarding.jsx` gates on Redux `user.personal_project_id` only:

- `personal_project_id` **null** -> Welcome card (ELITEA-2231; needs the `/social/author/` route mock).
- `personal_project_id` **set** -> `showTour=true` AND `thePrivateProjectIsReady=true`
  (effect at Onboarding.jsx:130-134) -> **tips card + "Your Elitea workspace is ready!" banner**.

So an ordinary authenticated user navigating **directly to `/onboarding`** lands in the
tour+ready state with **zero substitution**. The first-login (mocked) path can never show the
ready banner — with `personal_project_id` null the page stays on the progress footer. Never mock
author-details for tips-card cases.

## The side effect that bites the NEXT page

`handlePersonalProjectReady()` calls `markTourPending(FIRST_ELITEA_TOUR_ID)` ->
`localStorage["interactive-tour:first-elitea:pending"]="true"`. `useProposePendingTour` consumes
it on the next page, so landing on `/chat` after "Jump in now!" **always** opens the first-visit
prompt ("New here? ... Skip / Start!"), ignoring `prompt-seen`. It is a modal with a backdrop that
**intercepts pointer events** — the sidebar is visible but unclickable until Skip/Start/Escape
(Playwright reports `<div class="MuiBox-root ..."> intercepts pointer events`). It also logs
`MUI: The modal content node does not accept focus.` every open — filed as #1753.

## Duplicate testids in the fullscreen tour dialog

`OnboardingTour` keeps the embedded `TourContent` mounted while the fullscreen `Dialog` renders a
second copy: `onboarding-tour-tip-content` / `-page-indicator` / `-prev-button` each match **2
visible nodes** while open -> scope with `[data-testid="onboarding-tour-fullscreen-dialog"] [data-testid="..."]`.

Full handle cache: `test-specs/onboarding/_surface.md`.
