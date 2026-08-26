# Test Case: Settings → Personal Tokens shows the empty state when no tokens exist

## Metadata
- **TMS ID**: ELITEA-2250
- **Priority**: l2 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (auth via `auth_state` / `VITE_DEV_TOKEN` on localhost)
- **Analyst**: qa-engineer (Sage), batch `settings-w01`, 2026-08-24
- **Status**: **blocked** — "a user with no tokens created" is not obtainable on the local target, and the only way to fake it destroys irreplaceable shared test data
- **Surface digest**: `test-specs/settings-personal-tokens/_surface.md`
- **Filed**: none (no defect found on this surface this session)

## Why this is blocked (read this first)

Personal tokens are **user-scoped, not project-scoped** — `useTokenListQuery({ skip:
!user.personal_project_id })` (`PersonalTokens.jsx:32`) takes no project id, so
switching projects cannot change the list (verified live: the same 5 rows on every
project). The empty state therefore requires *the test user itself* to own zero
tokens.

Live inventory 2026-08-24, `/settings/tokens` (unchanged since the 2026-08-05
sessions that seeded this surface's digest):

| # | Token name | `data-expiration-state` | Label |
|---|---|---|---|
| 1 | `for_ui_tests` | `never` | Never |
| 2 | `Levon` | `never` | Never |
| 3 | `Marian` | **`expired`** | Expired |
| 4 | `New` | **`expired`** | Expired |
| 5 | `uautomate` | `never` | Never |

Routes checked, all fail:

1. **Delete all 5 tokens, assert the empty state, recreate them.** Rows 3 and 4 are
   **expired** — an expired token cannot be created (the create form only offers
   future expirations, per `create_personal_token_page.py` / the digest). Deleting
   them is irreversible and permanently breaks the merged
   `test_expired_token_shows_expired_icon_and_label` (ELITEA-2284), which reads the
   `expired` branch off exactly these rows. Token *values* are also shown once only,
   so `for_ui_tests` / `uautomate` (names that read as other people's fixtures)
   cannot be restored either.
2. **A second identity with no tokens.** `auth_state_user_b`
   (`automation/fixtures/session_fixtures.py:133`) exists but `pytest.skip`s on
   localhost by design ("Multi-user tests require deployed environment"), because
   localhost auth is the single `VITE_DEV_TOKEN` identity.
3. **Fabricate an empty token-list response** (`route.fulfill([])`) — a **terminal
   substitution**: the case's entire observable would be read off the test's own
   payload. Forbidden (`.agents/testing.md` § Fidelity policy); the case text asks
   for no simulation.

**Decision for the human:** either a dedicated token-free identity usable on the
local target (or run this case on a deployed env with such a user), or a ruling that
the case is manual-only. Everything else about the case is characterised below and
ready the moment an empty-token identity exists.

## Preconditions (as they would be, once unblocked)
- A logged-in user owning **zero** personal tokens.
- Any project may be selected — the list is user-scoped.

## Test Data
### reuse-existing (would be)
None — the case is about the absence of data.

## Test Steps (source-confirmed; step 1's precondition could not be met live)
1. Navigate to Settings → Personal Tokens (`/settings/tokens`) as a user with no
   tokens created.
   - **Blocked** — see above. Live navigation to the page was executed; only the
     zero-token precondition is missing.
   - **Timing note (confirmed live, matters for the implementer):** the page shows a
     `CircularProgress` (`role="progressbar"`, no testid) for ~2-2.5 s on every mount
     before either branch renders. Wait on the branch, never on a fixed delay.
2. Verify an empty-state message or illustration is shown.
   - **Verify**: `empty-state-title` has text `No tokens yet`; the description
     `Create your first API token.` is rendered; the illustration `<img>` is present.
   - Source: `PersonalTokens.jsx:296-306` → `EmptyStatePage`
     (`src/[fsd]/entities/empty-state-page/ui/EmptyStatePage.jsx`), title testid
     `empty-state-title` **already exists on main**; description and image carry none.
   - ⚠ **In this branch the page header does NOT render** — `PersonalTokens.jsx`
     returns the `EmptyStatePage` *before* `DrawerPage`, so
     `personal-tokens-page-title`, `personal-tokens-search-input`,
     `personal-tokens-add-button`, the table and all 4 action icons are **absent**.
     Do not assert any of them in the empty state.
3. Verify a "Create token" / "+" button is visible and accessible.
   - **Verify**: the `EmptyStatePage`'s own **`Create`** button (a `BaseBtn` with a
     plus icon, label text `Create`) is visible and enabled, and clicking it
     navigates to `/settings/create-personal-token` (`onCreateClick` →
     `onAddPersonalToken` → `RouteDefinitions.CreatePersonalToken`).
   - ⚠ **This button has NO testid** — `testid needed:
     `empty-state-create-button``, added as a caller-supplied `testId`-style prop on
     the SHARED `EmptyStatePage` (never hardcoded feature-scoped there —
     `.agents/testing.md` § shared components). `BaseBtn` already spreads unknown
     props to the DOM node, so the wiring is a prop thread, not a component rewrite.
   - The case's "+" wording refers to this button's plus icon; there is no separate
     header "+" in the empty state (see the warning in step 2).

## Handles Reference
| Element | Primary handle (testid-only) | Provenance | Notes |
|---|---|---|---|
| Empty-state title | `empty-state-title` | **on-main ✓** (`git grep` on `origin/main -- src/`, fetched 2026-08-24) | exact text `No tokens yet` |
| Empty-state Create button | **testid needed: `empty-state-create-button`** | needs-adding | caller-supplied prop on shared `EmptyStatePage`; used by every empty state in the app |
| Empty-state description | **testid needed: `empty-state-description`** (optional) | needs-adding | only if the case's "message" assertion should cover the description text too |
| Token row (absence proof) | `token-row` | **on-main ✓** | `to_have_count(0)` — but note the whole table is absent in this branch |
| Header add ("+") button | `personal-tokens-add-button` | **on-main ✓** | **absent** in the empty state — assert `to_have_count(0)`, never visibility |
| Create-token page title | `create-personal-token-page-title` (see digest) | see digest | destination proof after clicking Create |

## Coverage Map

### Axis 1 — every element of the TMS case
| Case element | Expected result (per live product) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | authenticated session | `auth_state` | fixture | covered |
| Step 1: navigate to Settings → Personal Tokens as a user with no tokens | `/settings/tokens` renders the empty branch | Step 1 | URL + branch | **blocked** — no zero-token identity available (§ Why this is blocked) |
| Step 2: empty-state message or illustration shown | `EmptyStatePage`: "No tokens yet" + "Create your first API token." + image | Step 2 | `empty-state-title` (+ description/image) | blocked on precondition; branch source-confirmed |
| Step 3: "Create token"/"+" visible and accessible | `EmptyStatePage`'s `Create` button (plus icon), navigates to `/settings/create-personal-token` | Step 3 | new `empty-state-create-button` + destination URL | blocked on precondition |
| Expected Final State: create button visible and accessible | as step 3 | Step 3 | same | blocked on precondition |

### Axis 2 — asserted beyond the case
| Observable | Why |
|---|---|
| the header/table/action icons are ABSENT in the empty state | the empty branch replaces the whole page; asserting absence pins the actual contract and stops a future "empty state + table" regression passing silently |
| the Create button actually reaches `/settings/create-personal-token` | "accessible" in the case text is otherwise untestable — a visible button that does nothing would pass a visibility-only assertion |
| no console errors | project standard; this surface was clean (0 errors) on every load this session |

## Known Defects / Clarifications
None found on this surface this session. The page behaved exactly as its digest
describes (5 rows, `showDownload` true, all 4 action icons, clean console).

## Blocked Steps
- **Step 1 — "as a user with no tokens created".** Needs a human decision: provision
  a token-free identity usable on the local target (or move the case to a deployed
  env where `auth_state_user_b` works and that user owns no tokens). Deleting the
  shared user's 5 tokens is not an option — two are expired and cannot be recreated,
  and ELITEA-2284's merged test depends on them.
