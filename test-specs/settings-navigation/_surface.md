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
PR's merge state, so they are live on the dev server regardless. Nothing left
for this cluster to add.

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
