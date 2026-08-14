---
name: Onboarding first-login state is reachable via an author-details route mock
description: How the whole onboarding case family gets its first-login precondition on localhost — D3 ruling, ELITEA-2231
type: project
---

The `onboarding` case family (11 cases, area issue #1397) all assert the
**first-login** state. On localhost `auth_state` bypasses login with a fixed
`VITE_DEV_TOKEN` user long past onboarding, so the state looks unreachable. It
is reachable, and this is the sanctioned way (lead ruling D3, ELITEA-2231,
2026-08-14).

## The product gate — every branch keys off ONE field

`user.personal_project_id`, sourced **only** from `GET /social/author/`
(`../EliteaUI/src/api/social.js:5,122` — `apiSlicePath='/social'`, RTK Query
`authorDetails`):

| Location | Behaviour |
|---|---|
| `src/[fsd]/app/routes/IndexRoute.jsx:15` | `!user.personal_project_id` → navigate `/onboarding`, else `/chat` |
| `src/pages/Onboarding/Onboarding.jsx:36` | `hasClickedGetStarted = sessionStorage.getItem('onboarding_state') === 'true'` |
| `src/pages/Onboarding/Onboarding.jsx:37` | `showTour = useState(hasClickedGetStarted \|\| !!user.personal_project_id)` |
| `src/pages/Onboarding/Onboarding.jsx:152` | `<Welcome>` renders iff `!showTour && !user.personal_project_id && user.id` |
| `src/[fsd]/app/layout/MainSidebar.jsx:42` | sidebar returns `null` iff `isOnboardingPage && !user.personal_project_id` |

## The mechanism

Intercept `**/social/author/`, **`route.fetch()` the genuine response**, then
re-`fulfill` with `personal_project_id` set to `null` and every other field
byte-identical. Route pattern as an UPPER_CASE class constant, interception in
a page-object `mock_*` method — the `generate_entity_modal_page_base.py:100-141`
shape. Shipped as `OnboardingPage.mock_fresh_user_state()` /
`clear_author_details_mock()` (`automation/pages/onboarding_page.py`).

**A synthetic response body is wrong** and was explicitly rejected: it makes
the "Hello, [Username]!" greeting a test of our own fixture. Mutating one field
of the real response keeps it an assertion about the real user's real name.

Install the mock **before** the first navigation, and navigate to the app
**root** (`navigate("/")`) so `IndexRoute.jsx:15` performs the redirect — going
straight to `/onboarding` bypasses the gate that is itself a case step.

## Declared coverage boundary — carry it forward

This verifies the first-login **UI** contract. It does **NOT** verify that the
backend returns `personal_project_id: null` for a brand-new user. That is an
owed, separate **API-level** case; no UI case in the family covers it. Never
let a UI case's green imply it.

## Why not a fresh user

`automation/routines/setup_test_users.py` cannot provide one — see
`setup_test_users_assumes_post_onboarding_state.md`.
