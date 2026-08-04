---
name: Interactive tours feature — zero testids + Help Center link /app-prefix quirk
description: Whole interactive-tours feature (17 tour configs) has no testids; Help Center resource links hardcode /app and 404 on localhost (harmless — overlay still works)
type: reference
---

Confirmed 2026-08-04, ELITEA-2227 (Help Center — Sidebar Interactive Tour).

- **`src/[fsd]/features/interactive-tours/` has ZERO `data-testid` attributes**
  anywhere (`find … -iname "*.jsx" | xargs grep -l "data-testid"` → no hits).
  This is the shared dialog/modal/spotlight chrome behind ALL 17 tour configs
  (`lib/constants/*Tour.constants.js` — sidebar, chat, agent, pipeline,
  artifact, mcp, users, ai-configuration, applications, notifications,
  personal-tokens, resources, secrets, toolkit, elitea-catalog, first-elitea).
  Any tour case needs the SAME generic testid set on `InteractiveTourCard.jsx` /
  `TourCompleteCard.jsx` / `TourCardHeader.jsx` / `InteractiveTourSpotlight.jsx`
  — `interactive-tour-title`, `-description`, `-step-counter`, `-skip-button`,
  `-back-button`, `-next-button` (ONE testid for Next/Finish — label flips, not
  the testid), `-spotlight`, `-complete-icon`, `-complete-title`,
  `-complete-keep-exploring-label`, `-complete-keep-exploring-{tourId}` (dynamic,
  keyed by the tour's OWN `tourId` — already exists as `data-tour-id` on that
  button, a clean stable key), `-complete-done-button`. Once ELITEA-2227's
  implementer adds these, every OTHER tour case (e.g. the Chat Interactive Tour,
  reachable from the same Tour Complete screen's "Keep exploring") needs ZERO
  new testids for the dialog chrome — only its own launch-link + keepExploring
  target, both already covered by dynamic templates (see below).

- **Tour target elements use `data-tour="<id>"` (via `buildTourSelector()`),
  NOT `data-testid`** — pre-existing, unrelated attribute system for the
  tour library's own spotlight targeting (`sidebarTourTargets.constants.js`
  etc.). Do NOT use it as an automation locator (violates testid-only policy);
  it's a trap because it LOOKS like a stable selector and already exists on
  every sidebar nav item.

- **Help Center resource links (`resources/index.jsx`, `useGetResourcesConfigQuery`)
  are backend-CMS data, not EliteaUI source** — `grep -rn '?tour=' src/` returns
  nothing. Every link's href hardcodes `/app` (e.g. `/app/chat?tour=sidebar`),
  correct for deployed envs, WRONG on localhost (`APP_PREFIX=""`). Clicking one
  (`target="_blank"`, opens a new tab) lands on `/app/chat` → "Page not found"
  main content locally — but the tour dialog/overlay still mounts and runs
  perfectly (it's route-independent global UI). Confirmed live through a full
  17-step tour + Back + Finish + Complete + Done: zero functional impact, only
  cosmetic. NOT a product defect (deployed envs never see this — the href
  matches their APP_PREFIX). Workaround for a case needing the exact resulting
  PAGE identity verified (not just "overlay closed"): navigate directly to
  `<page>?tour=<id>` respecting `APP_PREFIX` — confirmed this starts the
  identical tour via the same `useTourFromUrl` hook, on a page that resolves
  correctly. Use the real click + new-tab flow when the case's literal step 1
  IS "click the link" (need `page.expect_popup()`); use direct nav only when
  you specifically need post-tour page-identity assertions.
