---
name: Sidebar header — testids, badge oracle, and the first-visit-prompt myth
description: How to test the sidebar socket dot and notification bell honestly, and why the interactive-tour prompt never fires in the pytest suite
type: project
aliases: [sidebar header, socket dot, notification bell, first-visit prompt, unread count probe]
tags: [area/elitea-ui, type/gotcha]
created: 2026-08-24
updated: 2026-08-24
---

## The first-visit interactive-tour prompt cannot fire in the pytest suite

`NewChat.jsx:104` is the ONLY caller of `useProposePendingTour`, and the hook returns immediately
unless `localStorage["interactive-tour:first-elitea:pending"] === "true"` — written only by
`/onboarding`'s `handlePersonalProjectReady()`. On localhost `auth_state` returns an **empty storage
state** and `conftest.py` builds a fresh context per test, so a spec navigating straight to `/chat`
never sees the prompt (and gets 0 console errors). It only appears for specs that reach `/chat`
*through* `/onboarding` (ELITEA-2241's path). An analyst's Playwright-MCP profile is sticky and WILL
see it — treat "the prompt blocks the sidebar" in an AFS as profile-specific until checked.

## The bell badge's honest oracle

The red badge is `<circle fill="#D71616">` INSIDE the bell SVG (`BellIcon.jsx`), driven by
`setHasMessages(!!data?.total)` from
`GET …/notifications/notifications/prompt_lib/{personal_project_id}?only_new=true&only_total=true`.
Capture that response around the navigation (`SidebarHeaderPage.navigate_and_get_unread_total()`)
and assert `data-has-messages` against the real `total` — never mock the count (terminal
substitution: the badge IS the observable).

**URL disambiguation:** the count probe and the notification-CENTRE list fetch share the URL prefix.
`only_total=true` ⇒ the count probe; `sort_by=created_at` ⇒ the list (what `NotificationCenterPage`
keys off).

## Popover, not modal

`NotificationList.jsx` is a MUI `Popover` — no backdrop, closes on outside click / Escape too, and
MUI unmounts it (no `keepMounted`), so "closed" is `to_have_count(0)`. Its testid must go on the
**paper** via `slotProps.paper`, never on `<Popover>` (MUI puts it on the Modal root, which is
`position:fixed; inset:0` for every popover). Opening it does NOT mark anything read — the badge
survives open→close.

Related: [[project_briefing]]
