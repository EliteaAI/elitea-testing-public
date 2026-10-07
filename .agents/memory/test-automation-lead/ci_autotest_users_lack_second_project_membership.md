---
name: CI autotest_user_<n> accounts lack a second project membership
description: Any case needing a 2nd non-public project (fork/share/cross-project) is red in CI by data, not code — no implementer dispatch will fix it
type: feedback
---

## The gap

Every CI `autotest_user_<n>` (DEV matrix, `test-ui-dev.yml`/`test-ui-custom.yml`)
belongs to exactly **one** non-public project — their own `TEST_USER_PROJECT_<n>`
— plus the public project (id 1). `USERS_TEAM_PROJECT_ID` (`automation/config.py:215`,
default `"400"`, the one env var a resolver could prefer to find a *shared*
second project) is **never set** in any `test-ui-*.yml` workflow — grepped,
zero hits outside `config.py`'s own default and the ELITEA-2051 test file.

So any case whose precondition needs the acting CI user in a **second**
project (fork-to-different-project, cross-project share, "add this user to
another team") will fail in CI no matter how correct the test code is, unless
it hardcodes/discovers a project the acting user isn't actually a member of
(which is worse — see ELITEA-2051's PR #1931 history, a hardcoded-id bug) or
happens to run against a dev/local identity that *does* have 2 projects
(399→400 locally).

## What this means for triage

If a card's failure message is "the acting user belongs to no project usable
as a fork/share SOURCE" (or structurally identical — "no second project to
X from"): **don't dispatch an analyst/implementer to re-derive this.** It's
not a code bug — confirm with one `gh run view --job <id> --log | grep -i
"precondition unmet\|member"` to see which `autotest_user_<n>` ran and that
their membership list has exactly one non-public entry, then go straight to
filing a `question` (no project-CREATE REST endpoint is documented anywhere
in the `elitea-platform` skill, and the only membership-granting capability,
`AdminUsersPage.invite_users`, is a UI invite flow — not a safe or durable
thing to run every CI invocation, and I hold no `autotest_user_*`/admin
credentials in any sandbox `.env.test` to do it myself anyway).

**The fix, when a human picks it up:** one-time admin action — grant every
`autotest_user_1..9` membership in one shared second project on DEV — then
wire that project's id as a new `USERS_TEAM_PROJECT_ID` CI secret, mirroring
the existing per-user `TEST_USER_PROJECT_<n>` secret pattern. Needs DEV admin
access + GitHub Actions secrets write — neither available to any pipeline
agent. First hit: #2410/#2414 (ELITEA-2051, 2026-10-07).
