---
name: A brand-new testid resolving to 0 elements can be dev-server HMR lag
description: Before suspecting the JSX, probe the live DOM — a just-pushed testid can be missing from a pytest run started a minute later
type: project
aliases: [testid 0 elements, HMR lag, to_have_count 0 new testid, vite dev server stale]
tags: [area/flakiness, type/gotcha]
created: 2026-08-24
updated: 2026-08-24
---

## What happened

ELITEA-2252 (2026-08-24). A testid was added to `Profile.jsx`, committed and
pushed to `automation/testids`; the pytest run started ~1 minute later resolved
`get_by_test_id("settings-profile-logout-icon")` to **0 elements** across 14
polls / 5 s, while five other testids added in the *same* session (an earlier
commit) resolved fine in the same run. A direct Playwright probe moments later
dumped the button's `outerHTML` and the attribute was there.

## The move

When a **brand-new** testid resolves to 0 and older ones in the same file work:

1. Probe the live DOM first (`page.locator(<parent testid>).evaluate("el => el.outerHTML")`)
   — one throwaway script, ~10 s.
2. Attribute present ⇒ re-run. No code change, no locator change.
3. Attribute absent ⇒ then it is the JSX (wrong element, prop not spread, etc.).

The cost of getting this backwards is high: "fixing" a correct locator by
rungging down to a raw handle is exactly the drift the locator policy exists to
stop.

Related: [[svgr_icons_accept_testid_at_call_site]]
