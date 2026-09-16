# CI-user membership precondition class (ELITEA-2051 / #2320, 2026-09-16)

- DEV Stable assigns suites → `autotest_user_<n>` via the matrix builder (`test-ui-custom.yml` § Build test matrix); the user a suite runs as changes between runs.
- Only some autotest users have a non-public team project on DEV: `autotest_user_1` yes (fork test green), `autotest_user_2` NO (memberships = own private + public) → any case needing "a second project the acting user belongs to" flips red on user identity alone.
- Triage: `gh run view --job <id> --log | grep -oE "USERNAME=\"autotest_user_[a-z0-9]+\""` — do this before anything else on a "precondition unmet" [FIX] card. Cannot verify/repair from this machine (autotest creds + admin token are CI secrets).
- Open decision: #2327 (provision memberships + set `USERS_TEAM_PROJECT_ID` on DEV — recommended). Same latent hazard for ELITEA-2292 (`users_team_project_id`) and ELITEA-2399-2401 (`ai_providers_seeded_project_id`).

## Update 2026-09-16 (#2339)
Per-user tally now measured from `TEST_USER_EMAIL` in each DEV Stable `pipelines` job: **user_1 ✅, user_3 ✅, user_2 ❌**; users 4–9/admin unmeasured. Cheapest triage for any new `[FIX][ELITEA-2051] precondition unmet` card: (1) `gh issue list --label question … | grep 2051` → #2327 exists; (2) compare the card's `Run ID:` with #2320/#2333's — same run ⇒ `duplicate` + Blocked on #2327, different run ⇒ add an occurrence row on #2327 with the user, still `duplicate` of #2320. Never open the job logs before step (1).

## Update 2026-09-16 (#2341)
Run #168 → user 2 again (4th consecutive). Rate ~3 twins/day. Beware: `git log main..base -S"_resolve_source_project_id"` returns `9bb6badd5` (#1803) as if it were unpromoted — it reached main as `fa976fa54` (#1931) under a different SHA; trust the spec byte-diff, not the -S hit. Disposition unchanged until #2327 is answered.
