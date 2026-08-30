# Surface digest — settings-navigation

Confirmed live on `http://localhost:5173` (`EliteaAI/EliteaUI` `automation/testids`,
DEV backend), project `Private` (`${TEST_USER}`, project id 399), 2026-08-26.
Cluster: qa-engineer analyst, batch `settings-w01`, ELITEA-2242 / ELITEA-2243 /
ELITEA-2244 (one live session). Handle cache — verify a stale-looking entry
against the app before trusting it, don't treat this as a source of truth.

## Source of truth in code

- Drawer config: `SETTINGS_TABS_CONFIG` in `src/[fsd]/pages/settings/index.jsx`.
- Drawer rendering: `src/[fsd]/features/settings/ui/settings-drawer/SettingsDrawer.jsx`.
- Default-tab hardcode: the sidebar "Settings" button
  (`SettingsButton.jsx`) navigates to `.replace(':tab', 'project-general')`
  unconditionally — it does **not** remember the last-viewed tab. The bare
  `/settings` route also redirects to `project-general`
  (`<Navigate to="project-general" replace/>`, `ProtectedRoutes.jsx`).

## Case-text drift — tracked, don't re-file

**Clarification EliteaAI/elitea-testing-public#1772** (OPEN, `question` label)
already covers all of the following, filed for exactly this cluster
(ELITEA-2242/2243/2244). Do not file a duplicate — comment on #1772 if a new
occurrence surfaces.

| Case text | Live product |
|---|---|
| PROJECT = "AI Configuration, Project Params, Secrets, Users, Analytics" | PROJECT = **General, AI Providers, Project Context, Secrets, Users\*, Analytics\*, Usage\*** |
| PERSONAL = "Personalization, Personal Tokens, Notifications, Log out" | PERSONAL = **Profile, Preferences, AI Personality, Memory, Personal Tokens, Notifications** — no Log out anywhere in the drawer |
| "AI Configuration is selected and active by default" | Default landing tab is **General** (`project-general`), both via the sidebar Settings button and the bare `/settings` redirect |
| "Log out is visible as the last PERSONAL item" | No Log out item exists in the drawer at all (see `test-specs/settings-user-profile/_surface.md` for where Log out actually lives — Settings → Profile page content) |
| "Project Params" | No such page; nearest equivalents are **General** and **Project Context** |
| "Personalization" | Renamed to **Preferences**; a separate **AI Personality** page also exists |

\* **Conditionally rendered** (`index.jsx` `sections` filter) — confirmed live
on the `Private` project this session:
- **Users** — hidden when the selected project *is* the user's personal
  project (`showUsersSection = projectId != user.personal_project_id`).
  Absent on `Private` (confirmed: 6 PROJECT items observed, not 7).
- **Analytics** — hidden when `platformSettings.analytics_enabled === false`.
  Present this session.
- **Usage** — hidden unless `platformSettings.cost_budgets_enabled`. Present
  this session.
- **Project Context** — hidden on the Public project only. **Service
  Prompts** / **Environment** appear *only* on the Public project (not
  observed this session — Private project).
- **Secrets** — gated on `PERMISSIONS.secrets.list`. Present this session.

⇒ A spec asserting the PROJECT list should assert presence of the
project-independent core (General, AI Providers, Project Context, Secrets,
Analytics, Usage) and treat Users/Service Prompts/Environment as
project-dependent — never assert a literal item count without pinning the
project type.

## Testids — provenance (verified `git fetch origin` 2026-08-26)

| Testid | On `main`? | On `automation/testids`? | Notes |
|---|---|---|---|
| `settings-drawer` | no | yes — `EliteaAI/EliteaUI@e1e031a1` | Drawer root `<Box data-testid="settings-drawer">`, `SettingsDrawer.jsx` |
| `settings-drawer-menu` | no | yes — `EliteaAI/EliteaUI@e1e031a1` | Menu container inside the drawer (both PROJECT + PERSONAL groups render inside it) |
| `settings-nav-item-{tabId}` + `data-active` | no | yes — `EliteaAI/EliteaUI@e1e031a1` | Dynamic per-tab testid, `SettingsDrawer.jsx` `section.tabs.map`. `data-active="true"/"false"` carries selection state (PR #581 compliant — testid stable, state on the attribute). Class constant: `SETTINGS_NAV_ITEM = '[data-testid="settings-nav-item-{}"]'` |
| `settings-content` | no | yes — `EliteaAI/EliteaUI@e1e031a1` | Content pane `<Box component="main" data-testid="settings-content">`, `src/[fsd]/pages/settings/index.jsx`. **Required** — the page has TWO `<main>` elements (app shell + settings content); a bare `main` selector is ambiguous. |
| `sidebar-settings-button` | no | yes (added ELITEA-1807) | `BasePage.sidebar_settings_button`, pre-existing |

All four Settings-drawer testids were added in one commit,
`EliteaAI/EliteaUI@e1e031a1` ("[EL-2252] add data-testid for Settings drawer,
content pane and Profile logout button"), on a **different, not-yet-merged**
elitea-testing-public branch (`tests/ELITEA-2252-settings-profile-logout-visible`)
— but testids promote to `automation/testids` independently of the test-repo
PR's merge state, so they are live on the dev server regardless.

**Resolved/added during ELITEA-2242/2243/2244 implementation (2026-08-26):**
ELITEA-2242 step 2 needs a positive handle for the drawer's two group headers
("PROJECT"/"PERSONAL") — the analyst's exploration didn't need one (headers
weren't asserted individually), but the implementer's Coverage Map cross-check
found the AFS step required a real assertion target, and no testid existed on
the plain `<Box component="span">{section.section}</Box>` header nodes
(`SettingsDrawer.jsx`). Per `.agents/testing.md` § Locator policy ("Missing
testid on the target? That is work to do, not a reason to rung down"), added
`data-testid={`settings-section-header-${section.section.toLowerCase()}`}` —
`settings-section-header-project` / `settings-section-header-personal` — on
`automation/testids` (`EliteaAI/EliteaUI@529e2e4d`), not yet on `main`. Class
constant: `SettingsDrawerPage.SETTINGS_SECTION_HEADER =
'[data-testid="settings-section-header-{}"]'`. Also note: this JSX lives under
`src/[fsd]/` — the dev server served a stale module for this edit until a
manual restart (`vite_hmr_misses_fsd_bracket_dirs.md` /
`vite_dev_server_stale_on_onedrive.md` in
`.agents/memory/test-automation-engineer/` — the pattern recurred exactly as
documented; curl the served module before trusting a "0 elements" result on
any `src/[fsd]/` edit).

## Confirmed drawer inventory (Private project, this session)

**PROJECT** (`settings-nav-item-{id}`): `project-general` (General, **default
active**), `ai-providers` (AI Providers), `project-context` (Project Context),
`secrets` (Secrets), `analytics` (Analytics), `usage` (Usage). 6 items —
`users` absent (Private project).

**PERSONAL**: `profile` (Profile), `preferences` (Preferences),
`ai-personality` (AI Personality), `memory` (Memory), `tokens` (Personal
Tokens), `notifications` (Notifications). 6 items, ends at Notifications — **no
Log out node anywhere in the drawer** (confirmed via DOM query:
`document.querySelectorAll('[data-testid^="settings-nav-item-"]')` returns
exactly these 12, no 13th).

## Route map (clicking each nav item → URL)

| Tab id | Route | Page title |
|---|---|---|
| `project-general` | `/settings/project-general` | Settings: project-general |
| `ai-providers` | `/settings/ai-providers` | Settings: ai-providers |
| `project-context` | `/settings/project-context` | Settings: project-context |
| `secrets` | `/settings/secrets` | Settings: secrets |
| `analytics` | `/settings/analytics` | Settings: analytics |
| `usage` | `/settings/usage` | Settings: usage |
| `profile` | `/settings/profile` | Settings: profile |
| `preferences` | `/settings/preferences` | Settings: Preferences |
| `ai-personality` | `/settings/ai-personality` | Settings: ai-personality |
| `memory` | `/settings/memory` | Settings: memory |
| `tokens` | `/settings/tokens` | Settings: tokens |
| `notifications` | `/settings/notifications` | Settings: Notifications |

Every click produces a distinct URL and a distinct `settings-content` render
(confirmed one at a time, live, this session) — no dead clicks, no
stuck-on-previous-page.

## Default-tab-restore mechanism (ELITEA-2244)

The sidebar "Settings" button does **not** remember the last-viewed sub-tab —
it hardcodes `project-general` every time (`SettingsButton.jsx`). Confirmed
live: navigated to `/settings/secrets`, clicked "Agents" (away), clicked
"Settings" again → landed back on `/settings/project-general` (General),
**not** Secrets. This satisfies the case's literal intent ("restores the
default landing tab") — the drift is only in what the default tab is called
("AI Configuration" in the case text vs "General" live), not in the
mechanism.

## Console errors — known, filed, don't re-discover

- **EliteaAI/elitea-testing-public#1771** (OPEN, MINOR, filed for
  ELITEA-2243): `/settings/ai-personality` fires exactly one React DOM
  warning on every mount — `disableUnderline` prop leaking onto a native DOM
  node (`AIPersonalityPersonalization.jsx` → `StyledInputEnhancer.jsx` →
  MUI `OutlinedInput`). Confirmed live, deterministic, single-cause. A spec
  that visits AI Personality (ELITEA-2243's click-through) sees exactly this
  one error and no others; specs that don't visit AI Personality (ELITEA-2242,
  ELITEA-2244) see **zero** console errors.
- `/settings/secrets` did **not** reproduce
  EliteaAI/elitea-testing-public#1203 ("Maximum update depth exceeded") on a
  passive navigate-and-view this session — that defect is interaction-
  triggered (e.g. opening the create-secret dialog), not present on simple
  page load. Don't add a blanket #1203 filter to a spec that only navigates
  to Secrets without interacting further.

## AFS files from this run

- `l2_settings_page_sections_and_default_tab_ELITEA-2242.md` — ready-for-automation
- `l3_settings_sidebar_item_navigation_ELITEA-2243.md` — ready-for-automation (known-defect soft-assert for #1771)
- `l3_settings_default_landing_tab_restored_ELITEA-2244.md` — ready-for-automation

Not a family AFS — the three cases differ in **steps** (static inventory
check vs full click-through vs navigate-away-and-back), not only in data, so
each has its own spec per `test-case-analysis` SKILL.md § Execute. All three
share this digest and the same drift ticket (#1772).

**Resolved/added during ELITEA-2260 implementation (2026-08-26):** the drawer's
PERSONAL group renders **no badge or counter next to any item**, Notifications
included — `SettingsDrawer.jsx` renders `icon + label` only; verified live at both
1728x861 and the headless test viewport 1366x768 (drawer innerText carries no digit;
zero `MuiBadge` nodes inside `settings-drawer`). The product's unread indication is a
boolean red dot on the app sidebar header bell (`sidebar-notifications-bell-icon
[data-has-messages]`), covered by ELITEA-2234. Also confirmed: the whole 12-item menu
fits without scrolling at 1366x768 (`settings-drawer-menu` `scrollHeight ==
clientHeight == 617`, `scrollTop == 0`), so "last PERSONAL item visible without
scrolling" is a stable assertion at the framework viewport. ELITEA-2260's "unread count
badge" step is another occurrence of the #1772 drift — commented there, not re-filed.

---

## Role vantages on this surface (added 2026-08-30, batch `settings-w12`, ELITEA-2245/2246/2247)

**Roles are PROJECT-scoped**, and the shared `${TEST_USER}` (`testbot@elitea.ai`,
user id 659, `personal_project_id` **399**) genuinely holds different roles in
different projects — so a real admin/editor/viewer vantage is one project switch
away, no second identity and no substitution needed. Verified live 2026-08-30 via
`GET /api/v2/admin/users/prompt_lib/{pid}` + `GET /api/v2/auth/permissions/prompt_lib/{pid}`
(Bearer `ELITEA_API_TOKEN`, base `https://dev.elitea.ai/api/v2`):

| Project | id | role held | permissions | `*secret*` perms | Secrets in drawer? | Users in drawer? |
|---|---|---|---|---|---|---|
| UI Testing | **400** | **`admin`** | 360 | 8 | yes | **yes** |
| Private (personal project) | 399 (`settings.elitea_project_id`) | `editor`+`viewer` | 299 | 6 | yes | no (personal project) |
| Elitea Testing Team | 471 (`settings.elitea_team_project_id`) | `viewer` | 158 | 0 | **no** | yes |
| Bugs & Features | 406 | `viewer` | 158 | 0 | (not walked) | — |
| Elitea Development | 25 | `viewer` | 158 | 0 | (not walked) | — |

- **Project 400 is not yet in `config.py`.** ELITEA-2245/2247 ask for a new
  `elitea_admin_project_id` key (default `400`) + `.env.test` entry, mirroring the
  two existing project-id keys. Don't hardcode `400` in a spec.
- **There is no `Monitor` role.** `GET /api/v2/admin/roles/default/{pid}` returns
  exactly `['admin','editor','viewer']` for all five projects above. Any case step
  naming Monitor is **un-executable**, not skipped — clarification
  EliteaAI/elitea-testing-public#1909 (OPEN). Don't re-file.
- **Secrets presence in the drawer is the cheapest role-vantage guard**: present on
  400/399, `count 0` on 471. Use it to prove a project switch actually took effect
  before asserting anything role-dependent.
- **Users row action icons are the sharpest admin-only observable**:
  `user-row-edit-button` / `user-row-delete-button` render and are enabled on 400,
  and are permission-gated **out entirely** on the viewer projects
  (`test-specs/settings-users-and-roles/_surface.md` § Gotchas). Note the Users *nav
  item itself* IS offered to a viewer on 471 — only the actions disappear.

### Admin PROJECT walk on project 400 (ELITEA-2245, live 2026-08-30)

Drawer PROJECT order: `project-general`, `ai-providers`, `project-context`,
`secrets`, **`users`**, `analytics`, `usage` (7 — one more than the 6 seen on 399,
because Users renders when `projectId != personal_project_id`).

All 7 clicked one at a time: each reached `/settings/{tab}`, rendered a non-empty
`settings-content`, showed **no** access-denied text, and produced **zero** console
errors and **zero** 4xx/5xx `/api/v2/` responses.

Named interactive controls observed **enabled** per section (useful "editable fields
are interactive" anchors — all read-only assertions, no typing needed):

| Section | Handles |
|---|---|
| `project-general` | `project-general-section`, `ai-configurations`, `ai-configuration-accordion-summary`, `ai-configuration-tab-basic-button`, `default-modules-section`, `midturn-injection-section` (accordion summaries; the module **checkboxes inside have NO individual testids**) |
| `ai-providers` | `ai-providers-section-{llms,embedding-models,vector-storage,image-generation,asr,tts,ai-credentials}` accordion summaries |
| `secrets` | `secrets-search-input`, `secrets-add-button`, `secret-row`, `secret-row-visibility-toggle-button`, `secret-row-actions-button`, `secrets-pagination-*` |
| `users` | `users-search-input`, `users-invite-button`, `user-select-all-checkbox`, `user-row-checkbox`, `user-row-edit-button`, `user-row-delete-button`; header `users-header-edit-button`/`users-header-delete-button` are **correctly disabled** until a row is selected |
| `preferences` | `preferences-general-section-header`, `voice-personalization-voice-select`, `voice-personalization-{speed,volume}-slider-input`, `voice-preview-button`, `sound-notifications-*` |
| `tokens` | `personal-tokens-search-input`, `personal-tokens-add-button`, `token-action-preview-button`, `token-action-delete-button` |
| `notifications` | `notifications-search-input`, `notifications-select-all-checkbox`, `notification-checkbox-{id}` (dynamic), `notification-mark-toggle-button` / `notifications-delete-selected-button` (**disabled until a selection**) |

⇒ Never assert "zero disabled controls" on these pages — several are legitimately
disabled by design (pagination on page 1, batch actions before a selection).

### Runtime-composed testids — grep-invisible, not missing

The AI-Providers per-section default/tier **selector inputs** carry testids built
inside the shared section component as `` `${sectionTestId}-default-selector` ``
(live in the DOM as e.g. `ai-providers-section-llms-default-selector`), so
`git grep` of the literal string finds **nothing on either branch** while the
attribute is demonstrably present. Spec them as a class-level template constant
(`'[data-testid="ai-providers-section-{}-default-selector"]'`) — this is **not** a
missing testid and must not trigger `add-data-testid`.

### PERSONAL sections across vantages (ELITEA-2247, live 2026-08-30)

`preferences` ("Preferences" — the case text's "Personalization"), `tokens`
("Personal Tokens") and `notifications` ("Notifications Center") loaded cleanly in
**all three** vantages (admin@400, editor@399, viewer@471): correct route, non-empty
content, no denial text, no 403, **zero** console errors on all nine loads. Personal
settings are user-scoped, so no project role gates them.

### Viewer deep-link to Secrets — unchanged, still #1773 + #1203

`/settings/secrets` on project 471 renders the ordinary "No secrets" empty state
while `GET /api/v2/secrets/secrets/default/471` returns **403**, with no
access-denied UI (bug EliteaAI/elitea-testing-public#1773, OPEN) and the route also
fires `Maximum update depth exceeded` (#1203, OPEN — observed again this session).
A spec that merely *navigates* to Secrets on a permitted project sees neither.

### AFS files from this run

- `l3_admin-role-access-to-all-project-settings-sections_ELITEA-2245.md` — ready-for-automation
- `l2_all-roles-access-personal-settings-sections_ELITEA-2247.md` — ready-for-automation
- `test-specs/settings-secrets/lcovered_viewer-and-monitor-roles-cannot-access-secrets_ELITEA-2246.md` — **already-covered** by ELITEA-2348's merged spec (`automation/tests/ui/admin/test_viewer_role_cannot_access_secrets.py`); ELITEA-2246 and ELITEA-2348 are the same case body authored into two TMS folders

Not a family AFS — the three differ in **steps**, not only data.

---

## Resolved/added during ELITEA-2245 / ELITEA-2247 implementation (2026-08-30, implementer)

Attributed implementation-time facts only — none of the analyst's behavior or
scope claims above are changed.

### Testid added

| Testid | Where | Note |
|---|---|---|
| `project-general-edit-icon-button` | `ProjectParamsHeader.jsx`, EliteaAI/EliteaUI@e1f40532 on `automation/testids` (NOT on `main`) | The project-icon edit `IconButton` in Settings → General. **Permission-gated**: rendered only when `checkPermission('models.project_context.edit')` holds. Attribute-only addition — no DOM node, hook or structural change. |

### The section-container testids are NOT interactivity handles

`project-general-section`, `default-modules-section` and `ai-providers-section-llms`
sit on **`BasicAccordion` containers** (`<div>`), not on form controls. Playwright's
`to_be_enabled()` is **vacuously true** on any non-form element that carries no
`aria-disabled`, so an "accordion is enabled" assertion observes nothing. Use a real
control inside the section instead:

| Section | Non-vacuous interactivity handle |
|---|---|
| `project-general` | `project-general-edit-icon-button` (added above) |
| `ai-providers` | `ai-providers-section-llms-default-selector-combobox` — MUI marks a select trigger `aria-disabled` when disabled, which IS what `to_be_enabled()` reads |
| `default-modules-section` | none — its module switches carry no individual testids; assert *visible* only |

`BasicAccordion` defaults `defaultExpanded = true`, so every accordion's contents
ARE mounted on load — no expand click is needed to reach a control inside one.

### Project Context empty state (project 400, 2026-08-30)

Project 400 carries no project context, so `/settings/project-context` renders its
empty state, whose **entire** testid inventory is two CTAs:
`project-context-create-button` and `project-context-build-with-ai-button`.
There is **no `project-context-page-title` testid in this state** — a spec that
anchors on the page title there will fail. The non-empty state offers a different
control (`project-context-edit-button`) instead.

### `models.project_context.*` permissions, live (Bearer `ELITEA_API_TOKEN`)

| Project | `project_context` permissions |
|---|---|
| 400 (admin) | `view`, `generate`, `edit` |
| 399 (editor+viewer) | `view`, `generate`, `edit` |
| 471 (viewer) | `view` only |

So `project-general-edit-icon-button` is present on 400/399 and absent on 471 —
a usable role-discriminating observable on the General section, alongside the
Secrets nav entry the analyst already documented.

### Project switching on a `/settings/*` route

Use `BasePage.ensure_project_selected(project_id)`, **not** `switch_project()`:
the latter settles on `wait_for_network()` + a fixed 1 s pause, which is the
`#1847` mechanism (the persistent `/socket.io/` poll makes `networkidle` a race).
`ensure_project_selected` waits on the two project-scoped GETs the switch actually
fires and no-ops when the project is already active — which also makes it the right
call for an unconditional teardown restore. Navigate to the settings route FIRST:
the `page` fixture starts on a blank page, so the sidebar selector must exist
before it can be clicked.

### Environment gotcha — Vite can serve a STALE transform of a just-edited file

A newly added testid did not reach the browser even though it was on disk and the
dev server was running: `curl`ing the module straight from Vite returned the OLD
transform, and `touch`ing the file did not invalidate it. The watcher had missed the
change (this repo lives on OneDrive, and the source tree uses bracketed `[fsd]`
directory names — both are known watcher hazards). **Restarting `npm run dev` fixed
it**, and the served module then contained the testid.

Cheap check before blaming a test for "testid not found" on a *just-added* testid:

```bash
curl -s "http://localhost:5173/src/%5Bfsd%5D/<path-to>.jsx" | grep -c "<your-testid>"
```

`0` means the dev server is stale, not that the component fails to render it. This
cost one full rerun of ELITEA-2245's spec.

### Zero console errors / zero API failures — confirmed at implementation time

The analyst's "zero across all sections" measurements held: the 7-section admin
PROJECT walk and all 9 (3 roles × 3 sections) PERSONAL loads ran with **strict zero**
console errors and **zero** `/api/v2/` 4xx/5xx, over 4 clean invocations. In
particular the `#1971` project-id-less toolkit 404 — whose documented trigger IS a
project switch — did **not** fire on any of these runs, so neither spec opts into
`exclude_known_defect_urls`. If it starts appearing, that opt-in (URL-keyed, with a
`# Known defect: #1971` comment) is the sanctioned response.
