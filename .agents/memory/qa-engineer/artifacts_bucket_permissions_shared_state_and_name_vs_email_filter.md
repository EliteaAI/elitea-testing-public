---
name: Artifacts bucket-permissions — shared state + name-vs-email autocomplete filter
description: ELITEA-2493/2494 triage findings — Add-exceptions autocomplete filters by display name not email; the real hazard is a globally-shared bucket+user never cleaned up
type: project
---

Confirmed live on DEV (2026-10-08, ELITEA-2493 triage, issue #2419) while investigating
a 3/3-red `test_no_access_permission_blocks_all_api_operations`
(`automation/tests/ui/artifacts/test_bucket_permissions_api.py`).

## The Add-exceptions autocomplete filters/renders by DISPLAY NAME, not email

Frontend source (origin/main): `AddBucketUserDialog.jsx` builds
`availableUsers` as `{...u, name: u.name || u.email}`; `UserSearchSelect.jsx`
passes `nameField="name"` into `AutoCompleteDropDown.jsx`, whose MUI
`createFilterOptions()` (default, case-insensitive substring) filters against
`getOptionLabel(option) = option[nameField]`. So typed text is matched against
the user's **display name**, with email only used as the label when a user's
`name` field happens to be empty. Live-fetched project-470 member list: 32 of
34 members have a real human/duplicated-username name (`"autotest_user_9
autotest_user_9"`, `"Alexander Bychinskiy"`, …) that is NOT their email; only 2
(`autotest_user_2@centry.user`, `autotest_user_6@centry.user`) have
`name == email`.

**This does NOT break `add_permission_exception()` as currently written**,
because the real CI `TEST_USER_B_EMAIL` value is the bare string
`autotest_user_9` (not an email — `.github/workflows/test-ui-custom.yml:529`),
which IS a substring of that account's real name. But if anyone ever
"fixes" that env var to a real `@epam.com` email address (looks like a bug,
isn't), the search would break for exactly this reason. Don't retype it to an
email without checking this.

**The `.fill()`-not-firing-React-onChange gotcha (`CLAUDE.md`/`mui-patterns.md`)
does NOT apply to this specific Autocomplete** — live A/B test: `.fill()` and
`press_sequentially()` produced byte-identical filtering results. That gotcha
is real for some MUI fields in this app but is not universal; verify live
before citing it as the cause of a given timeout.

## The real hazard: one shared bucket + one shared "User B", never cleaned up

`BUCKET_NAME = "permissionstest"` is a hardcoded constant shared by BOTH tests
in this file (ELITEA-2493 "No access" and ELITEA-2494 "Read-only"), and the
`test_bucket` fixture only deletes it if the fixture itself created it — once
created the first time, it is NEVER deleted again by any later run. `User B`
(`autotest_user_9`) is explicitly documented as shared across **every**
parallel CI matrix job (`test-ui-custom.yml:527`: "uses user 9 for all
parallel jobs"). Found this bucket live, BEFORE touching anything, already
carrying a stale `Exceptions – 1 / autotest_user_9 / Read-only` row — leftover
from a prior run's incomplete cleanup. The pre-clean-and-retry logic in both
tests only guards "I already have a leftover from MYSELF"; it has no defense
against a sibling test / concurrent run perturbing the same bucket+user
between its own remove and re-add steps. A manual, slowly-paced replay of
remove→reopen→add worked fine (no timeout) — the component isn't broken, the
isolation story is. Recommended fix for whoever touches this file: give the
bucket a unique per-run name (pattern already used elsewhere, e.g.
ELITEA-1866's `test-bucket-<timestamp>-<random>`), which makes the whole
pre-clean branch unnecessary.

## Playwright MCP `chrome` channel binary not present in this sandbox

`npx playwright install chrome` appeared to run but didn't actually fetch
anything reachable here (no `/opt/google/chrome/chrome` after). Worked around
by driving the browser directly via the project's own already-installed
chromium (`/opt/ms-playwright/chromium-1243`, the one `pytest-playwright`
itself uses — no `channel=` override anywhere in `conftest.py`/`config.py`)
through a small ad-hoc `sync_playwright()` script reusing
`.playwright-mcp/dev-storage-state.json`. Legitimate tool-substitution per
`test-case-analysis` § Execute ("switching tools mid-case is fine") when the
MCP's dedicated channel isn't available in a given sandbox.
