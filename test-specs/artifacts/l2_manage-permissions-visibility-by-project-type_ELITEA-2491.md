# Test Case: "Manage permissions" Bucket-Menu Visibility by Project Type

## Metadata
- **TMS ID**: ELITEA-2491 ("Manage Access Not Visible in Private and Public Projects")
- **Linked Story**: `EliteaAI/elitea_issues#5832`, `EliteaAI/elitea_issues#5912` (case `requirements:`)
- **Priority**: l2 (TMS `priority: high`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`, DEV backend)
- **User set**: n/a — localhost `auth_state` skips login (`VITE_DEV_TOKEN`); acting user is the standard `${TEST_USER}` (`personal_project_id = 399`)
- **Analyst**: qa-engineer (analyst slot, batch `artifacts-w06`, 2026-08-23)
- **Status**: **blocked** — steps 12-15 (Public project) cannot be executed by the acting user; see § Blocked Steps. Steps 1-11 were executed live and are fully specced below, ready to implement the moment a human rules on the Public scope (`EliteaAI/elitea-testing-public#1699`).

## Preconditions
- Acting user is logged in (localhost `auth_state`).
- **Team project** with at least one bucket — satisfied read-only by
  `Elitea Testing Team` (**id 471**, `settings.elitea_team_project_id`): 11 bucket
  rows rendered live 2026-08-23.
- **Private project** with at least one bucket — satisfied read-only by the acting
  user's personal project (**id 399**, rendered as `Private`): 1044 bucket rows
  rendered live (the `#636` bucket leak keeps growing it).
- **Public project** with at least one bucket — **NOT SATISFIABLE** (§ Blocked Steps).
- Nothing is seeded and nothing is mutated: the whole case is menu-visibility
  observation on existing buckets (workflow skill Hard Rule 10). The bucket used in
  each project is chosen at run time as the first rendered row, never a literal name.

## Test Data
### existing-stable (read-only)
| Field | Value | Note |
|---|---|---|
| Team project | `471` — `Elitea Testing Team` | from `settings.elitea_team_project_id`, never hardcoded in the spec |
| Private project | `399` — `Private` | from `settings.elitea_project_id` |
| Bucket (either project) | first rendered row, resolved at run time | e.g. `abc-test` in 471, `aa` in 399 on 2026-08-23 |

The case's "Bugs & Features" test-data suggestion is **not** used: it is project `406`,
also a Team project, but `471` is the project the suite already configures for
team-scoped work (`settings.elitea_team_project_id`, `test_bucket_permissions_api.py`).

## Concrete Handles

| Element | Handle | Provenance |
|---|---|---|
| Sidebar project selector trigger | `project-selector-trigger-combobox` (`BasePage.project_selector_trigger`) | pre-existing — `on-main ✓` |
| Project option in the selector | `select-option-{project_id}` (dynamic — `BasePage.SELECT_OPTION`) | pre-existing — `on-main ✓` |
| Bucket row | `artifacts-bucket-row-{name}` (dynamic — `ArtifactsPage.BUCKET_ROW`) | pre-existing — `on-main ✓` |
| Bucket row 3-dot menu button | `bucket-menu-{name}-menu-button` (dynamic — `ArtifactsPage.BUCKET_MENU_BUTTON`) | pre-existing, composed at runtime by `DotMenu.jsx:354` — invisible to a `data-testid`-literal grep |
| Open dot-menu container | `bucket-menu-{name}-menu` (dynamic — `ArtifactsPage.BUCKET_MENU_CONTAINER`) | pre-existing |
| **"Manage permissions" menu item** | **`testid needed: bucket-menu-manage-permissions-menuitem`** | **needs-adding** — see below |
| Buckets page heading (page-load gate) | `artifacts-buckets-heading` | pre-existing — `on-main ✓` |

### The one testid to add

`src/pages/Artifacts/Components/BucketItem.jsx`'s `menuItems` array gives the
`Manage permissions` entry **no `key`**, and `DotMenu` derives a menu item's testid
from exactly that (`DotMenu.jsx:422` `testId: item.key` → `DotMenu.jsx:58`
`data-testid={testId}-menuitem`). Live confirmation, Team project 471:

```
 [0] bucket-menu-upload-files-menuitem  "Upload files"
 [1] bucket-menu-rename-menuitem        "Rename"
 [2] bucket-menu-pin-menuitem           "Pin to top"
 [3] testid=None                        "Share"
 [4] testid=None                        "Manage permissions"
```

Implementer work (via `add-data-testid`, on `automation/testids`): add
`key: 'bucket-menu-manage-permissions'` to that one menu-item object — the exact
shape ELITEA-1820 already used for the pin item. This yields
`data-testid="bucket-menu-manage-permissions-menuitem"`.

- **Do NOT also key the `Share` item.** It is on no test's executed path in this
  case (canon #511 — add only the testid your test calls).
- **One testid, two assertions.** The Team step asserts it is visible, the Private
  step asserts `to_have_count(0)` scoped inside the open menu container. Absence
  assertions count as references (`.agents/testing.md` § Locator policy) — this is
  what makes the Private-side assertion honest instead of a text grep.
- No `data-*` state attribute is involved: the item is structurally rendered or
  filtered out (`display: 'none'` entries are dropped by `menuItems`' own
  `.filter(...)` before render), not merely hidden.

## Test Steps

Reference implementation shape — one `allure.step` per numbered step below.
Existing page-object methods cover everything except the new testid:
`BasePage.switch_project()`, `ArtifactsPage.navigate_to_artifacts()`,
`wait_for_page_load()`, `get_rendered_bucket_names()`, `open_bucket_menu()`,
`bucket_menu_container()`.

| # | Action | Expected (live-confirmed unless marked) |
|---|--------|------------------------------------------|
| 1 | Navigate to `/artifacts` (localhost `auth_state`); wait for `artifacts-buckets-heading` | Artifacts page loads; project selector reads `Private` by default |
| 2 | `switch_project(settings.elitea_team_project_id)` (471) | Selector reflects `Elitea Testing Team`; bucket list reloads |
| 3 | Resolve the first rendered bucket row; hover it | `bucket-menu-{name}-menu-button` becomes visible (hover-gated) |
| 4 | Click the menu button | `bucket-menu-{name}-menu` is visible |
| 5 | Assert `bucket-menu-manage-permissions-menuitem` **is visible** inside that container, and its text is exactly `Manage permissions` | Item present. Full live menu text in 471: `Upload filesRenamePin to topShareManage permissions` (5 items) |
| 6 | Press `Escape` | Menu container no longer visible (live-confirmed) |
| 7 | `switch_project(settings.elitea_project_id)` (399, `Private`) | Selector reads `Private`; bucket list reloads |
| 8 | Resolve the first rendered bucket row; hover it | Menu button visible |
| 9 | Click the menu button | Menu container visible |
| 10 | Assert `bucket-menu-manage-permissions-menuitem` has **count 0** inside that container **and** assert the container's own text does not contain `Manage permissions` | Item absent. Full live menu text in 399: `Upload filesRenamePin to topDelete` (4 items) |
| 11 | Press `Escape` | Menu closes |
| 12-15 | **Public project** — switch, open Artifacts, open a bucket's dot-menu, assert the item is absent | **BLOCKED — not executable, see § Blocked Steps** |

Side channel: assert no unexpected console errors across the run. Live baseline in the
Team-project run was clean; the Private-project run produced the project's known
background `404`/`403` noise (`.agents/testing.md` § Known issues — the `secrets 403`
exclusion class), so the console assertion must use the suite's existing filter, not a
bare `assert not console_messages`.

## Expected Results
1. In a **Team** project the bucket dot-menu contains `Manage permissions` (and `Share`).
2. In the **Private** (personal) project the same menu contains neither — it holds
   `Upload files`, `Rename`, `Pin to top`, `Delete`.
3. In a **Public** project the item is expected (per case text) to be absent — **unverified,
   and the code says otherwise** (§ Findings).

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — Login | Login successful | localhost `auth_state` transit (`VITE_DEV_TOKEN`) | implicit — page load in Step 1 | covered (transit) |
| Step 2 — Navigate to a Team project | Project opens | Step 2 | selector state + bucket list reload | covered |
| Step 3 — Go to Artifacts, select a bucket | Bucket selected | Steps 1+3 | `artifacts-buckets-heading`, row resolved | covered |
| Step 4 — Click context menu (3 dots) | Context menu opens | Step 4 | `bucket-menu-{name}-menu` visible | covered |
| Step 5 — "Manage access" IS present (Team) | visible | Step 5 | `bucket-menu-manage-permissions-menuitem` visible | covered — **label drift**: live label is `Manage permissions` (`EliteaAI/elitea-testing-public#1698`) |
| Step 6 — Close context menu | Menu closes | Step 6 | container not visible | covered |
| Step 7 — Navigate to a Private project | Project opens | Step 7 | selector reads `Private` | covered |
| Step 8 — Go to Artifacts, select a bucket | Bucket selected | Step 8 | row resolved | covered |
| Step 9 — Click context menu | Menu opens | Step 9 | container visible | covered |
| Step 10 — "Manage access" NOT present (Private) | absent | Step 10 | `to_have_count(0)` + container-text check | covered |
| Step 11 — Close context menu | Menu closes | Step 11 | container not visible | covered |
| Step 12 — Navigate to a Public project | Project opens | — | — | **blocked** (§ Blocked Steps, `#1699`) |
| Step 13 — Go to Artifacts, select a bucket | Bucket selected | — | — | **blocked** |
| Step 14 — Click context menu | Menu opens | — | — | **blocked** |
| Step 15 — "Manage access" NOT present (Public) | absent | — | — | **blocked** — and contradicted by a static code reading (§ Findings) |
| Precondition — "access to a Private/Public/Team project with at least one bucket" | — | Private ✓ (399), Team ✓ (471), Public ✗ | § Preconditions | partially blocked |
| Pass criterion — present in Team | — | Step 5 | | covered |
| Pass criterion — absent in Private | — | Step 10 | | covered |
| Pass criterion — absent in Public | — | — | | **blocked** |

### Axis 2 — observables asserted beyond the case
| Extra observable | Why |
|---|---|
| Exact item label `Manage permissions` (not just presence) | the case's own label is stale; pinning the live string is what makes `#1698` self-correcting |
| Full menu-item set per project (`5` items in Team, `4` in Private) | a container-text assertion catches the sibling `Share` item disappearing/appearing too — the same `isPersonalProject` gate drives both, so one regression would otherwise slip past a single-item check |
| Console side channel (filtered) | § Test Steps — silent errors are the ones that ship |

## Fidelity Declaration

**No substitution of any kind.** Every observable is produced by the live product:
real project switching through the sidebar selector, real hover + click on the real
dot-menu, real DOM read of the rendered menu. No `page.route`, no `evaluate`, no
injected state, no API-seeded precondition.

One diagnostic — forcing the stored project id to `1` to test whether the Public
project could be entered at all — was run **during exploration only**, produced no
assertion, and is recorded in § Blocked Steps as evidence that no honest route exists.
It must **not** appear in the implemented test.

## Blocked Steps

**Steps 12-15 (Public project) cannot be executed — filed as `EliteaAI/elitea-testing-public#1699`.**

What was verified live, 2026-08-23:

1. `useProjectType.hooks.js` defines the three project types strictly by id:
   `isPrivate = id === personal_project_id`, `isPublic = id === PUBLIC_PROJECT_ID`,
   `isTeam = neither`.
2. `PUBLIC_PROJECT_ID` is **1** — visible in the selector's own feed request,
   `GET /api/v2/projects/project/default/1?check_public_role=true`.
3. That request returns, for the acting user, exactly: `400 UI Testing`,
   `471 Elitea Testing Team`, `25 Elitea Development`, `399 project_user_659`
   (`Private`), `406 Bugs & Features`. **Project 1 is absent** — the user has no
   public role. The sidebar selector renders those 5 options and no other.
4. There is no alternative user-facing route: project selection is redux +
   `localStorage`/`sessionStorage`. Forcing the stored ids to `1` and reloading did
   **not** switch the app (it stayed on `Private`, 1044 `Private` buckets, requests
   still `?project_id=399`).

**To unblock, a human must choose one of:**
- **Re-scope the case** to the verifiable contract (visible in Team, absent in
  Private) and drop/split the Public steps → this AFS is implementable as-is,
  steps 1-11, with the Coverage Map's blocked rows removed.
- **Provision Public-project access** for the automation user (public role on
  project 1) → the full 15 steps become executable, and step 15 will then decide
  whether § Findings' code reading is a real product bug.

Automation must not manufacture the Public context (forced storage, API-seeded
project, mocked project list) — that is a terminal substitution of the very thing
the case observes (`.agents/testing.md` § Fidelity policy).

## Findings

1. **Case-text drift — the item is `Manage permissions`, not `Manage access`**
   (`EliteaAI/elitea-testing-public#1698`). The string "Manage access" exists nowhere
   in `EliteaUI/src`; only the internal handler `handleManageAccessClick` carries the
   old name. Same family as #666/#650 (this menu's `Rename`-vs-`Edit` drift).
2. **The case's Public expectation is probably wrong — code reading, unverified**
   (`EliteaAI/elitea-testing-public#1699`). `BucketItem.jsx` gates BOTH `Share` and
   `Manage permissions` on a single condition —
   `display: isPersonalProject ? 'none' : undefined`, where
   `isPersonalProject = projectId === personal_project_id`. There is **no `isPublic`
   check anywhere in this menu.** In the Public project `isPersonalProject` is
   `false`, so `Manage permissions` would render — i.e. the product hides it in the
   **Private** project only, not in "Private and Public" as the case title claims.
   Filed as a clarification, not a `bug`, precisely because it could not be observed
   live.
3. **The Team project's menu has no `Delete` item** (5 items, not the 6 the digest's
   ELITEA-1820 note predicted). `canDelete = isPrivate || checkPermission(artifacts.delete)`
   — the acting user holds no `artifacts.delete` permission in project 471. Not a case
   observable, but it means "a Team project's menu has 6 items" is user/permission
   dependent: never assert a fixed Team-menu item count, assert the specific item.
4. **`Escape` closes the dot-menu** in both projects (live-confirmed) — cheaper and
   less flaky than clicking elsewhere for the case's "Close context menu" steps.

## Live-execution evidence (2026-08-23, localhost:5173)

```
===== team-471 (Elitea Testing Team) =====
bucket rows rendered: 11 · first bucket: abc-test
menu container visible: True
menu text: 'Upload filesRenamePin to topShareManage permissions'
 [0] bucket-menu-upload-files-menuitem 'Upload files'
 [1] bucket-menu-rename-menuitem       'Rename'
 [2] bucket-menu-pin-menuitem          'Pin to top'
 [3] testid=None                       'Share'
 [4] testid=None                       'Manage permissions'
menu after Escape visible: False

===== private-399 (Private) =====
bucket rows rendered: 1044 · first bucket: aa
menu container visible: True
menu text: 'Upload filesRenamePin to topDelete'
 [0] bucket-menu-upload-files-menuitem 'Upload files'
 [1] bucket-menu-rename-menuitem       'Rename'
 [2] bucket-menu-pin-menuitem          'Pin to top'
 [3] bucket-menu-delete-menuitem       'Delete'
menu after Escape visible: False

===== public (id 1) =====
NOT REACHABLE — absent from GET /api/v2/projects/project/default/1?check_public_role=true
and from the selector (5 options: 399, 406, 25, 471, 400). Forced storage id did not switch.
```

Screenshots: `/tmp/e2491/menu-team-471.png`, `/tmp/e2491/menu-private-399.png`
(exploration scratch — not committed evidence).
