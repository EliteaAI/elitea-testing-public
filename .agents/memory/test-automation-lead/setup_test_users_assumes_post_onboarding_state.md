---
name: setup_test_users assumes the post-onboarding state
description: The suite's user tooling is deployed-env-only and errors when a user has no personal_project_id — no fresh-user path exists
type: project
---

`automation/routines/setup_test_users.py` looks like a fresh-user mechanism.
It is not. Verified 2026-08-14 (ELITEA-2231):

- **Deployed envs only** — `ENV_URLS` covers STAGE2 / STAGE3 / DEV / NEXT.
  **No localhost entry.**
- **Logs in existing users** — `USERNAME_TEMPLATE = "autotest_user_{index}"`.
  It does **not create** users.
- Reads `personal_project_id` from `GET /api/v2/auth/user` (`:102-113`, used at
  `:317`) and **errors when the user has none** (`:319`).
- It never resets `personal_project_id`.

So the suite's own user tooling **assumes the post-onboarding state**. Any case
needing a genuine pre-onboarding user needs backend capability that does not
exist today (no create-user, no reset-field). Treat "just use a fresh test
user" as a real follow-up requiring a backend ask — not as an available option
to hand an analyst or implementer.

Consequence for the onboarding family: the state is established by route
interception instead — see
`onboarding_first_login_state_is_reachable_via_author_details_mock.md`.
