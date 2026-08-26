---
name: A testid added inside one conditional render branch silently narrows which rows a locator can reach
description: When a new testid lands on a branch of an `if (x) return <A/>; return <B/>` component, any row hitting the other branch has NO such node — the locator times out opaquely instead of failing on a named precondition
type: feedback
aliases: [conditional render testid, legacy branch no testid, locator timeout on some rows, testid only on one branch]
tags: [area/ui, type/gotcha]
created: 2026-08-26
updated: 2026-08-26
---

## The trap

Review checks ask "is the testid on a stable element?" and "is it referenced on the
executed path?" — neither asks **which subset of rows actually renders it**. A
component that early-returns one JSX tree and falls through to another renders the
new testid on only one of them.

Worked example (ELITEA-2258, PR #1785): `NotificationListItemMessage.jsx` renders
`<Typography data-testid={testId}>` only `if (notification.meta?.message)`; otherwise
it delegates to `LegacyNotificationMessage`, which has no such node. The spec picks
its subject rows straight off the API response (`unread_ids[0]`, `unread_ids[1]`)
with no filter, so a legacy-shaped row would make `get_row_message_color()` sit on a
10 s `wait_for` and die with `Timeout waiting for locator`, not with the loud named
precondition failure the AFS promised for every other precondition.

## What to check as reviewer

1. Open the component the new testid landed in and count its **return statements**.
   More than one ⇒ ask which data shape reaches which branch.
2. If the spec selects its subject dynamically from an API payload, the selection
   predicate must include whatever makes the testid render (here: `row.get("meta", {}).get("message")`),
   with a loud assertion when nothing qualifies.
3. Never accept "it passed live today" for this class — the deciding field is data,
   and the account's data grows.

Failure mode is a confusing red, not a false green, so it is Important-not-Critical —
but it costs a debug cycle in the hardening gate, and a one-line filter removes it.

Related: [[absence_assertions_can_pass_vacuously]]
