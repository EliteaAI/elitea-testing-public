# Surface digest — Help Center / Interactive Tours

Confirmed live 2026-08-04 against `http://localhost:5173` (`automation/testids`
build). Update this file, don't replace it, as later cases confirm/drift.

## Feature location (EliteaUI source)
- Help Center page: `src/[fsd]/pages/resources/index.jsx` (+ `ui/ResourceCard.jsx`,
  `ui/ResourceVersionInfo.jsx`). Route: `/help-center` (no `/app` prefix needed on
  localhost — respects `APP_PREFIX` normally, unlike the tour *links* below).
- Interactive tours feature (shared by ALL tour types — chat, agent, pipeline,
  artifact, mcp, users, ai-configuration, applications, notifications,
  personal-tokens, resources, secrets, toolkit, elitea-catalog, first-elitea,
  sidebar): `src/[fsd]/features/interactive-tours/`.
  - `ui/InteractiveTourRoot.jsx` — phase switch: `prompt` | `running` | `complete`.
  - `ui/InteractiveTourCard.jsx` — the running-tour dialog (title, description,
    counter, Skip/Back/Next-or-Finish).
  - `ui/TourCompleteCard.jsx` + `ui/TourCardHeader.jsx` — the completion modal
    (icon, title, "Keep exploring:" options, "Done!").
  - `ui/InteractiveTourSpotlight.jsx` — the highlight overlay; a plain `Box`
    positioned via inline styles from the target element's bounding rect.
  - `lib/constants/<name>Tour.constants.js` — one file per tour, `steps[]` array
    of `{id, target, title, content, skip?}`. `sidebarTour.constants.js` has 17
    steps (enumerated in the AFS `l2_sidebar-interactive-tour-completes_ELITEA-2227.md`).
  - `lib/constants/sidebarTourTargets.constants.js` — maps step ids to
    `[data-tour="…"]` selectors via `buildTourSelector()`. **`data-tour` is a
    pre-existing, non-testid attribute already on every sidebar element** — do
    NOT use it as a locator (policy is testid-only); it's documented here only
    so the next analyst doesn't mistake it for a usable handle.
  - `lib/hooks/useTourFromUrl.hooks.js` — starts a tour when `?tour=<id>` is in
    the URL. Confirmed: works identically whether reached by clicking a Help
    Center resource link or by direct navigation to `<page>?tour=<id>`.

## Testid inventory — as of this session
**Zero `data-testid` attributes exist anywhere under
`src/[fsd]/features/interactive-tours/`** (confirmed via
`find … -iname "*.jsx" | xargs grep -l "data-testid"` → no hits). This whole
feature area is testid-free; every tour-dialog / tour-complete-modal case will
need the generic testids listed in the ELITEA-2227 AFS's Concrete Handles table
(`interactive-tour-*` / `interactive-tour-complete-*` — NOT tour-specific, they
back every tour config).

Help Center page itself also has zero testids. Sidebar nav items (Chats, Agents,
Pipelines, Skills, Toolkits, MCPs, Credentials, Applications, Artifacts,
Settings, Catalog, Help Center, Notifications, Support Assistant, Logo) have
**no testids either** — only 3 unrelated sidebar elements do:
`project-selector-trigger`, `sidebar-toggle`, `sidebar-create-button`.

## Known quirk — Help Center resource links hardcode `/app` prefix
The "Sidebar Interactive Tour" / "Chat Interactive Tour" links on the Help
Center page (`href="/app/chat?tour=sidebar"` etc.) are **backend-CMS-served
data** (`useGetResourcesConfigQuery`), not EliteaUI source — grep for
`?tour=` in `src/` returns nothing, confirming this. The href always includes
`/app`, which is correct on deployed envs (`APP_PREFIX=/app`) but WRONG on
localhost (`APP_PREFIX=""`): clicking it opens a new tab (`target="_blank"`) to
`/app/chat` which localhost has no route for → "Page not found" in the main
content area, **but the tour dialog itself still mounts and runs correctly**
(it's a global overlay independent of route matching). Confirmed live: full
17-step tour + Back + Finish + Tour Complete + Done all work normally on that
"Page not found" background. Not a product defect — a localhost-only URL
artifact. Direct navigation to `<page>?tour=<id>` (respecting `APP_PREFIX`) is
the workaround if a future case needs the resulting page's *identity* verified
(e.g. "returns to project default page view" asserted by literal page content,
not just "overlay closed"). Full reasoning: ELITEA-2227 AFS § Automation Hints.

## Reusable pattern for the NEXT tour case (e.g. "Chat Interactive Tour")
- Same `InteractiveTourCard` / `TourCompleteCard` / `InteractiveTourSpotlight`
  testids apply verbatim (generic, not sidebar-specific) — once added by
  ELITEA-2227's implementer, no new testid work needed for other tours' dialog
  chrome.
- Only the tour-specific pieces need new testids: the resource-link that
  launches it (dynamic `help-center-tour-link-{slug}` — already covers ALL
  resource links via the templated pattern, so likely zero new work), and
  whatever `keepExploring` target the NEW tour's complete-screen shows (dynamic
  `interactive-tour-complete-keep-exploring-{tourId}` — same story).
- Step content reference for the chat tour: not yet explored — read
  `src/[fsd]/features/interactive-tours/lib/constants/chatTour.constants.js`
  (seen in passing during this session: its `keepExploring` includes
  `{label: 'Sidebar Interactive Tour', tourId: 'sidebar'}`, so the two tours
  cross-link each other's completion screens).
