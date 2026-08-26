---
name: Version-number literals are flaky assertions
description: Asserting exact live backend/component semver strings pins the test to values that legitimately change on redeploy
type: feedback
---

Found reviewing ELITEA-2225 (`test_help_center_version_info.py`) — the Help Center
version-info tooltip shows each backend component's name + live semver
(`elitea_core: 0.673`, `admin: 0.77`, ...) sourced from `useGetSystemInfoQuery`
(`systemInfo.plugins`). The AFS captured these as "live-confirmed" values during
analysis and the test hardcodes them as literal expected strings (both in the
tooltip-text regex and the clipboard-content check).

**Why this is a real flakiness risk, not a hypothetical one:** these are actual
deployed-service version numbers — the exact kind of data that bumps on every
release of any of the 6 listed components. Unlike an agent/skill "version 1 →
version 2" (a stable entity property under test control), this is infrastructure
metadata outside the test's control. The very next backend deploy that ships a
patch to any one of those 6 services turns this test red for a reason that has
nothing to do with a regression.

**Better pattern for this class of assertion:** verify presence + format
(`re.compile(rf"{component}:\s*\d+\.\d+")`) rather than a pinned literal, or — if
exact fidelity matters (as it does here, since the case's real intent is "the
copied text matches what the tooltip showed") — fetch the current live value at
test time (via the same API the page calls, or by reading the tooltip text first)
and assert the CLIPBOARD matches the TOOLTIP, rather than assert both against a
value captured once during analysis and frozen into the test file.

**When reviewing any "displays current version/build info" feature**: treat
hardcoded version-like literals as a standing check, same weight as selector
stability — grep the diff for suspiciously precise numeric literals paired with
words like `version`, `build`, `release`.
