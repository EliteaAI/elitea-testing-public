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

## Resolved/added during ELITEA-2220/2221/2222/2223/2224 implementation (2026-08-14)

These 5 cases cover the OTHER resource-card links (Documentation, Release Notes,
Video Library, Tutorials) — not the Interactive Tours card, which ELITEA-2227
already covers. `src/[fsd]/pages/resources/index.jsx` renders link testids the
SAME way for every card (`RESOURCE_CARD_CONFIGS.map` → `links.map`), so
everything below composes with the tour-link inventory above under the SAME
`help-center-tour-link-{slug}` naming.

- **Fixed a real testid collision**: the Video Library card's and the
  Tutorials card's "More..." links both slugify to `help-center-tour-link-more`
  (bare-title slugify has no card-awareness) — `page.locator(...)` matched 2
  elements page-wide. Fixed on `automation/testids` by adding a
  `testidCategory` field to each `RESOURCE_CARD_CONFIGS` entry and prefixing
  ONLY the generic "More..." title's slug with it:
  `help-center-tour-link-video-library-more` /
  `help-center-tour-link-tutorials-more`. Every other card's link testids
  (including ELITEA-2227's `sidebar-interactive-tour` / `chat-interactive-tour`)
  are byte-identical — verify via
  `document.querySelectorAll('[data-testid^="help-center-tour-link-"]')` and
  check for duplicate values before trusting a bare-title-slug testid on this
  page. If a future card is added with another generic CTA title, check for
  this collision class again.
- **Full live-confirmed link inventory** (all resolve to real `href`s, backend
  CMS-driven via `useGetResourcesConfigQuery`, confirmed 2026-08-14):
  - Documentation: `getting-started` → `docs.elitea.ai/getting-started/chat-quick-start`;
    `how-to-guides` → `.../how-tos/chat-conversations/how-to-use-chat-functionality`;
    `integrations` → `.../integrations/mcp/create-and-use-server-stdio`;
    `migration-update` → `.../support/faqs`. All load correctly.
  - Release Notes: `release-2-0-2-latest` → `.../release-notes/rn-2-0-2` —
    **404, known defect `EliteaAI/elitea-testing-public#1492`** (docs site's
    actual latest is `rn-2-0-5`; the resources CMS "latest" config is stale).
    `release-2-0-1` / `release-2-0-0` / `release-2-0-0b2` all load correctly
    (archived releases unaffected).
  - Video Library: 4 named video links → `videoportal.epam.com/video/dYo2peva#t=<offset>`
    (not explored further — out of scope for this session's cases);
    `video-library-more` → `videoportal.epam.com/channel/DdYPoMVa2X/videos` —
    **requires EPAM corporate SSO** (`access.epam.com`), no credentials exist
    anywhere in this project. Any future case touching Video Library's channel
    content is blocked the same way ELITEA-2223 was — don't re-discover this,
    treat it as a standing environment limitation.
  - Tutorials: `course-ai-based-elitea-platform` → `learn.epam.com/catalog/...`
    (not explored — EPAM internal LMS, likely the same SSO wall if content
    verification is ever needed); `how-to-create-an-agent` →
    `docs.elitea.ai/archive/create-agent`, loads correctly;
    `how-to-create-a-pipeline` → `docs.elitea.ai/how-tos/pipelines/overview`
    (not explored further); `tutorials-more` → `docs.elitea.ai/` (the general
    docs homepage, NOT a dedicated tutorials-list page — case-text drift,
    filed as a CLARIFICATION reasoning in the AFS, not a bug).
- **Third-party destination pages are NOT subject to the testid-only locator
  policy** — that policy governs only our own `EliteaUI`/`elitea_assistant`
  source. Assertions against `docs.elitea.ai` / `videoportal.epam.com` use
  ordinary Playwright role/title locators (e.g.
  `new_page.get_by_role("navigation", name="Pages")` on the docs site).

## Resolved/added during ELITEA-2225 implementation (2026-08-14)

- **New surface within the already-mapped page**: `ResourceVersionInfo.jsx`
  (top-right of the Help Center header) — the version label + info-icon
  tooltip + copy-to-clipboard, previously only named in this digest's
  Feature location list, never explored. Data source:
  `useGetResourcesConfigQuery` (version/date) + `useGetSystemInfoQuery`
  (the 6 component versions: elitea_core, admin, notifications,
  configurations, sdk_plugin, indexer_worker) — both resolved by the time the
  header renders, no loading-state race observed live.
- **4 new testids added**, all direct attributes on existing JSX nodes (zero
  new DOM, confirmed via the Step 5.5 greps): `help-center-version-label`,
  `help-center-version-info-icon`, `help-center-version-info-tooltip`,
  `help-center-version-info-copy-button`. `EliteaAI/EliteaUI@bc82bc32` on
  `automation/testids`; NOT yet on `main` (human cherry-pick pending).
- **Interaction mode is HOVER, not click** — the case text says "Click the
  'i' icon" but the live `<Tooltip>` (MUI default trigger) opens on hover;
  no separate click handler exists. Not a defect (a click also works, since
  hover fires first) — automated as `hover()` per the interaction-discovery
  ladder; see the AFS Axis 2 note for the full reasoning. **Reusable finding
  for any future Help Center tooltip work**: don't assume click-to-open on
  MUI `Tooltip` instances here.
- **Reused the app-wide `toast-alert`/`toast-message` testids** (pre-existing,
  `src/components/Toast.jsx`) rather than adding new ones — same
  per-page-object-field declaration precedent as `AgentDetailPage`/`ChatPage`.
  Toast text confirmed live: "The version information has been copied to the
  clipboard."
- **Clipboard read-back works out of the box**: `conftest.py`'s `context`
  fixture already grants `clipboard-read`/`clipboard-write` globally — no
  per-test permission setup needed. Copied text format confirmed from source:
  `Version: X.Y.Z (DD-Mon-YYYY)\n<component>: <version>\n...` (one line per
  plugin, `—` em-dash fallback for a missing version — not hit live,
  all 6 components had real version strings).
