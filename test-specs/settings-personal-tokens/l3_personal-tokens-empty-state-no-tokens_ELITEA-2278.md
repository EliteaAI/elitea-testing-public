# Test Case: Personal Tokens page shows empty state when no tokens exist

## Metadata
- **TMS ID**: ELITEA-2278
- **Source case**: `.agents/automation/settings-w04/cases/ELITEA-2278.md` (intake snapshot)
- **Priority**: l3 (case frontmatter `priority: medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on
  `automation/testids` → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}` = 399)
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), batch `settings-w04`, cluster session, 2026-08-27
- **Status**: **blocked** — the precondition "a user with no tokens created" is not
  obtainable on the local target, and every route to fake it either destroys
  irreplaceable shared data or is a terminal substitution.
- **Surface digest**: `test-specs/settings-personal-tokens/_surface.md`
- **Filed**: none new — **already tracked** as issue **#1780**
  (`[QUESTION][ELITEA-2249/2250] Settings empty-state preconditions unobtainable for the
  shared ${TEST_USER} on localhost`). This case's occurrence was commented onto #1780
  rather than filed separately, per `.agents/profile.md` § Bug filing (a real duplicate
  found before filing ⇒ comment, don't file).

## ⚠️ This case is a near-duplicate of ELITEA-2250

`ELITEA-2250` ("Personal Tokens page shows empty state when no tokens exist") was
analysed on 2026-08-24 and parked `blocked` for exactly this reason —
`test-specs/settings-personal-tokens/l2_personal-tokens-empty-state-no-tokens_ELITEA-2250.md`.
ELITEA-2278 has the same title, the same objective, and the same three steps modulo
wording ("+ button" vs "Create token / + button"). **Neither is `already-covered`**:
`already-covered` requires a spec *merged to base* proving the observable, and no such
spec exists — 2250 produced an AFS, never a test. The two cases should be **merged in
the TMS**; flagged as a finding to the lead.

Everything below is a re-verification against the live product on 2026-08-27, not a copy
— the block was re-confirmed, not assumed.

## Why this is blocked (re-verified live 2026-08-27)

**Tokens are user-scoped, not project-scoped.** `useTokenListQuery({ skip:
!user.personal_project_id })` (`PersonalTokens.jsx:32`) takes no project id, so switching
projects cannot empty the list. The empty branch requires *the test user itself* to own
zero tokens.

Live inventory read this session (`/settings/tokens`, `token-row` × 5) — **unchanged
since 2026-08-05**:

| # | Token name | `data-expiration-state` | Label |
|---|---|---|---|
| 1 | `for_ui_tests` | `never` | Never |
| 2 | `Levon` | `never` | Never |
| 3 | `Marian` | **`expired`** | Expired |
| 4 | `New` | **`expired`** | Expired |
| 5 | `uautomate` | `never` | Never |

Routes checked, all fail:

1. **Delete all 5, assert the empty state, recreate them.** Rows 3–4 are **expired**, and
   an expired token cannot be created (the create form offers only future expirations).
   Deleting them permanently breaks the merged
   `test_expired_token_shows_expired_icon_and_label` (ELITEA-2284), which reads its
   `expired` branch off exactly these rows. Token *values* are shown once only, so
   `for_ui_tests` / `uautomate` (other people's fixtures, by name) cannot be restored
   either. Irreversible destruction, not a precondition.
2. **A second identity owning no tokens.** `auth_state_user_b`
   (`automation/fixtures/session_fixtures.py:133`) `pytest.skip`s on localhost **by
   design** — localhost auth is the single `VITE_DEV_TOKEN` identity.
3. **Fabricate an empty token-list response** (`route.fulfill([])`). **Terminal
   substitution** — the case's entire observable would be read off the test's own
   payload. Forbidden (`.agents/testing.md` § Fidelity policy); the case text asks for no
   simulation.
4. **NEW this session — reach it via the search box.** Typing a non-matching term does
   empty the table, but it renders a **different component**: `GridTableContainer`'s
   `isEmpty` message `"No tokens"` (`GridTableContainer.jsx:37-45`), with the column
   headers unmounted and the page header retained. Confirmed live that
   `empty-state-title` is **absent** in that state. The case's observable
   (`EmptyStatePage`, "No tokens yet" + illustration + Create button) is **not** produced
   by this route — asserting it here would be reading the wrong observable off the wrong
   branch. Recorded so nobody tries it as a shortcut.

**Decision for the human (same as #1780):** provision a token-free identity usable on the
local target, or run this case on a deployed env with such a user, or rule the case
manual-only. Everything else is characterised below and ready the moment such an
identity exists.

## Preconditions (as they would be, once unblocked)
- A logged-in user owning **zero** personal tokens.
- Any project may be selected — the list is user-scoped.

## Test Data
None — the case is about the absence of data.

## Test Steps (source-confirmed; step 1's precondition could not be met live)

1. Navigate to `${BASE_URL}/settings/tokens` as a user with no tokens created.
   - **Blocked** — see above. Live navigation was executed this session; only the
     zero-token precondition is missing.
   - **Timing (confirmed live):** a `CircularProgress` (`role="progressbar"`, no testid)
     covers the page for ~2–2.5 s on every mount before either branch renders. Wait on
     the branch, never on a fixed delay.

2. Verify an empty-state illustration **or** message is shown — not a blank area or a
   raw empty table.
   - **Verify**: `empty-state-title` has exact text `No tokens yet`; the description
     `Create your first API token.` renders; the illustration `<img>` is present.
   - Source: `PersonalTokens.jsx:296-306` → shared `EmptyStatePage`
     (`src/[fsd]/entities/empty-state-page/ui/EmptyStatePage.jsx`).
   - ⚠️ **In this branch the page header does NOT render** — `PersonalTokens.jsx` returns
     the `EmptyStatePage` *before* `DrawerPage`, so `personal-tokens-page-title`,
     `personal-tokens-search-input`, `personal-tokens-add-button`, the four
     `personal-token-column-header-*` and every `token-row` are **absent**. Assert their
     **absence** (`to_have_count(0)`), never their invisibility.

3. Verify the "+" button is still visible and accessible in the empty state.
   - **Verify**: the `EmptyStatePage`'s own **`Create`** button (a `BaseBtn` with a plus
     icon) is visible and enabled, and clicking it navigates to
     `/settings/create-personal-token` (`onCreateClick` → `onAddPersonalToken` →
     `RouteDefinitions.CreatePersonalToken`).
   - ⚠️ **This button has no testid** — `testid needed: `empty-state-create-button``,
     added as a **caller-supplied** `testId`-style prop on the shared `EmptyStatePage`
     (never hardcoded feature-scoped there — `.agents/testing.md` § shared components).
     `BaseBtn` already spreads unknown props to the DOM node, so it is a prop thread, not
     a component rewrite.
   - The case's "+" wording refers to *this* button's plus icon. There is **no** header
     "+" in the empty state (see the step-2 warning) — a test asserting
     `personal-tokens-add-button` here would be asserting the wrong element.

## Handles Reference

| Element | Primary handle (testid-only) | Provenance | Notes |
|---|---|---|---|
| Empty-state title | `empty-state-title` | **on-main ✓** (per ELITEA-2250's verified row, 2026-08-24) | exact text `No tokens yet` |
| Empty-state Create button | **testid needed: `empty-state-create-button`** | needs-adding | caller-supplied prop on shared `EmptyStatePage`; benefits every empty state app-wide |
| Empty-state description | **testid needed: `empty-state-description`** | needs-adding | only if the "message" assertion should cover the description text |
| Header add ("+") button | `personal-tokens-add-button` | on-`automation/testids` | **absent** in this branch — `to_have_count(0)` |
| Token row (absence proof) | `token-row` | on-`automation/testids` | `to_have_count(0)` |
| Create-token page title | `create-personal-token-page-title` | see digest | destination proof after clicking Create |

## Coverage Map

### Axis 1 — every element of the TMS case
| Case element | Expected result (per live product) | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: logged in | authenticated session | `auth_state` | fixture | covered |
| Step 1: navigate as a user with **no tokens** | `/settings/tokens` renders the empty branch | Step 1 | URL + branch | **blocked** — no zero-token identity (§ Why this is blocked) |
| Step 2: empty-state illustration or message shown | `EmptyStatePage`: "No tokens yet" + "Create your first API token." + image | Step 2 | `empty-state-title` (+ description/image) | blocked on precondition; branch source-confirmed |
| Step 3: "+" button still visible and accessible | `EmptyStatePage`'s `Create` button; navigates to `/settings/create-personal-token` | Step 3 | new `empty-state-create-button` + destination URL | blocked on precondition |
| Expected Final State: "+" visible and accessible | as step 3 | Step 3 | same | blocked on precondition |

### Axis 2 — asserted beyond the case (once unblocked)
| Observable | Why |
|---|---|
| header / search / table / column headers / rows are **absent** in the empty branch | the empty branch replaces the whole page; asserting absence pins the real contract and stops a future "empty state + table" regression passing silently |
| the Create button actually reaches `/settings/create-personal-token` | "accessible" is otherwise untestable — a visible button that does nothing would pass a visibility-only assertion |
| the no-match **search** state is a different component and must not be substituted for this one | documented here because it is the obvious wrong shortcut (see route 4 above) |
| no console errors | project standard; surface clean live |

## Known Defects / Clarifications
No product defect. Two findings for the lead:
1. **TMS duplication** — ELITEA-2278 and ELITEA-2250 are the same case; recommend merging
   them upstream so one block decision covers both.
2. The blocker itself is already tracked as **#1780** and unchanged.

## Blocked Steps
- **Step 1 — "as a user with no tokens created".** Needs a human decision: provision a
  token-free identity usable on the local target, move the case to a deployed env where
  `auth_state_user_b` works and that user owns no tokens, or rule the case manual-only.
  Deleting the shared user's 5 tokens is not an option — two are expired and cannot be
  recreated, and ELITEA-2284's merged test depends on them. Tracked on **#1780**.
