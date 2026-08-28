# Test Case: Profile section shows the correct user avatar, display name and email

## Metadata
- **TMS ID**: ELITEA-2373
- **Priority**: l3 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` on `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (auth via `auth_state` / `VITE_DEV_TOKEN` on localhost)
- **Analyst**: qa-engineer (Sage), batch `settings-w08`, cluster ELITEA-2371/2372/2373/2380/2387, 2026-08-28
- **Status**: ready-for-automation (**case-text drift — asserts the LIVE contract**)
- **Surface digest**: `test-specs/settings-user-profile/_surface.md`
- **Filed**: clarification **#1960**
- **Reuse**: `automation/pages/settings_profile_page.py` (`SettingsProfilePage`, ELITEA-2252) already
  models the drawer + `settings-profile-page`. **Extend that page object**; this is a new spec, not an
  extension of `test_settings_profile_logout_button_visible.py` — that spec asserts the logout button
  only and proves none of this case's observables.

---

## ⚠️ Case-text drift — read this before implementing

| Case text | Live product (verified 2026-08-28) |
|---|---|
| "Navigate to Personalization" and read the profile area "at the top of the page" | `/settings/personalization` **404s**. The avatar / display name / email live on **Settings → Profile** (`/settings/profile`), rendered by `src/[fsd]/features/settings/ui/profile/Profile.jsx` |
| Step 2: "the avatar **image** is shown (not a broken image icon)" | `UserAvatar` renders an `<img>` **only when `state.user.avatar` is set**. The shared test user (`Test Bot`) has **no** avatar URL, so the live render is the MUI `Avatar` **initials fallback** — text `TB`, zero `<img>` nodes inside `settings-profile-page` (verified live). |

Per the reverse-masking guard the spec asserts the **live** contract: *an avatar element
is rendered and is non-empty in whichever branch applies* (see Step 2). Asserting
`img[src]` unconditionally would be asserting the stale case text and would go red on a
correct product.

---

## Preconditions
- User logged in (`auth_state`; login skipped on localhost via `VITE_DEV_TOKEN`).
- Read-only case: nothing seeded, nothing written, no cleanup.
- Ground truth for the email is **external to the UI**: `settings.test_user_email`
  (`automation/config.py:101`, sourced from `.env.test`). Verified this session that it
  equals the account the localhost dev token authenticates as — asserting the UI against
  it is a real check, not a tautology.

## Test Data
### reuse-existing
`settings.test_user_email`. No `TEST_USER_NAME` key exists in config — see Step 3 for how
the display name is grounded without inventing one.

---

## Test Steps

### Step 1 — Open Settings → Profile
Navigate through the drawer (`settings-nav-item-profile`) so the case's "navigate to the
profile area" intent is exercised through the real UI path, not a deep link.
**Expected:** `settings-profile-page` visible; page header text `Profile`;
`settings-nav-item-profile` has `data-active="true"`.

### Step 2 — Verify an avatar is rendered (not a broken image)
**Expected (live contract, both branches):**
- `settings-profile-avatar` is visible;
- **and** exactly one of:
  - it contains an `<img>` whose `naturalWidth > 0` (real avatar — *not* the current test
    user's state), **or**
  - it has no `<img>` child and its text equals the user's initials (`getInitials(name)`),
    which for `Test Bot` is `TB` (verified live).
- The initials must be **non-empty** — an empty `Avatar` is the real failure mode this
  step guards (it is what `UserAvatar` renders when `name` is falsy).

Implementer note: assert the branch that is live, but derive it from the DOM
(`img` count) rather than hardcoding "no image" — the shared account could gain an avatar.

### Step 3 — Verify the display name
`Profile.jsx` renders the name **twice**: once under the avatar, once as the
`Full name:` field value.
**Expected:**
- `settings-profile-display-name` is visible and non-empty;
- it equals the `Full name:` field value (`settings-profile-fullname-value`) — an
  internal-consistency invariant that catches either render drifting;
- it equals the avatar's initials source: `getInitials(display_name) == avatar_initials`
  when the initials branch is live.

This is how the name is grounded without a config key for it. (An API tie-break —
`GET /api/v2/social/author/` via the framework's API client — is a legitimate stronger
oracle if the implementer wants one; the browser-side `fetch` used during analysis was
unauthenticated, so it was **not** used as evidence here.)

### Step 4 — Verify the email matches the logged-in user
**Expected:** `settings-profile-email-value` text == `settings.test_user_email`
(live: `testbot@elitea.ai`, matching `.env.test`).

### Step 5 — Side channel
**Expected:** no console errors on `/settings/profile`. Verified live: **0 errors** across
every load of this route this session (the #1771 `disableUnderline` warning fires on
`/settings/memory` and `/settings/ai-personality`, **not** here — do not add that filter
to this spec; it would be masking).

---

## Concrete Handles

| Element | Handle | Provenance (verified `git fetch origin`, 2026-08-28) |
|---|---|---|
| Profile page root | `settings-profile-page` | on `automation/testids` (EliteaAI/EliteaUI@e1e031a1); not on `main` |
| Profile nav item | `settings-nav-item-profile` (+ `data-active`) | on `automation/testids`; not on `main` |
| Avatar | `settings-profile-avatar` | **testid needed** — `Profile.jsx:44` `<UserAvatar … testId="settings-profile-avatar">`. `UserAvatar` already accepts `testId` and applies it in **both** branches (`src/components/UserAvatar.jsx:20,38`) — pure prop pass-through, no new node |
| Display name (under avatar) | `settings-profile-display-name` | **testid needed** — `Profile.jsx:49` `<Typography>{name}</Typography>`, pure attribute add |
| `Full name:` value | `settings-profile-fullname-value` | **testid needed** — `FieldWithCopy` has **no** testid plumbing today; add a `testId` prop to `FieldWithCopy.jsx` and land it on the value `<Typography>` (existing node), then name it at the **call site** in `Profile.jsx`. Caller-supplied prop = the compliant shape for a shared-ish component (`.agents/testing.md` § Locator policy) |
| `Email:` value | `settings-profile-email-value` | **testid needed** — same `FieldWithCopy` prop, named at the call site |

⚠️ **Do not add a feature-scoped testid inside `FieldWithCopy` itself** — it is reused by
the AI Providers page. Plumb the prop; name it at the call site.

⚠️ **Never click the Log out button** from this spec (`SettingsProfilePage` docstring
warning): `onLogout` sets `window.location.href = <origin>/forward-auth/logout` and parks
the context outside the SPA.

---

## Coverage Map

### Axis 1 — every element of the TMS case

| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1 — Navigate to Personalization | page loads | Step 1 (`/settings/profile` via the drawer) | page-root + active-tab assertions | **clarification #1960** — case route 404s |
| Step 2 — avatar image shown, not broken | avatar renders | Step 2 | visible + branch assertion + non-empty initials | covered (**live contract**: initials fallback for this user) |
| Step 3 — display name matches the logged-in user | name correct | Step 3 | non-empty + equals `Full name:` + matches initials | covered |
| Step 4 — email matches the logged-in user's address | email correct | Step 4 | equals `settings.test_user_email` | covered |

### Axis 2 — observables asserted beyond the case

| Extra observable | Why |
|---|---|
| The two renders of the name agree with each other | The case's "matches the logged-in user" has no config oracle for the name; this invariant is the strongest honest substitute and catches a real regression (one render drifting) |
| Active drawer tab is `profile` | Pins that Step 1's navigation actually landed, so Steps 2–4 cannot read a stale page |
| Zero console errors | Side-channel discipline; verified achievable on this route |

---

## Known traps

- **Avatar branch.** `<img>` vs initials depends on account state, not on the product being
  broken. Assert the branch you find, never `img` unconditionally.
- **Name appears twice** in `settings-profile-page` — a text-based locator would match both.
- **`FieldWithCopy` value has an `onClick` copy handler** — a stray click fires a toast and
  writes the clipboard. Read text, don't click.
- **Email is real test-account data**, not a secret, but it comes from `.env.test`: reference
  `settings.test_user_email`, never hardcode it in the spec.
