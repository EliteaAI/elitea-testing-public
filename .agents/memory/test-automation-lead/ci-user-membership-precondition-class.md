# CI-user membership precondition class (ELITEA-2051 / #2320, 2026-09-16)

- DEV Stable assigns suites → `autotest_user_<n>` via the matrix builder (`test-ui-custom.yml` § Build test matrix); the user a suite runs as changes between runs.
- Only some autotest users have a non-public team project on DEV: `autotest_user_1` yes (fork test green), `autotest_user_2` NO (memberships = own private + public) → any case needing "a second project the acting user belongs to" flips red on user identity alone.
- Triage: `gh run view --job <id> --log | grep -oE "USERNAME=\"autotest_user_[a-z0-9]+\""` — do this before anything else on a "precondition unmet" [FIX] card. Cannot verify/repair from this machine (autotest creds + admin token are CI secrets).
- Open decision: #2327 (provision memberships + set `USERS_TEAM_PROJECT_ID` on DEV — recommended). Same latent hazard for ELITEA-2292 (`users_team_project_id`) and ELITEA-2399-2401 (`ai_providers_seeded_project_id`).
