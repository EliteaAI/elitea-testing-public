---
name: Notification read/unread visual signal
description: Read vs unread notifications differ only by computed colour on the inner Typography — assert the difference, not rgb values
type: reference
aliases: [notification unread styling, is_seen colour, notification-message-text colour]
tags: [area/settings-notifications, type/handle]
created: 2026-08-26
updated: 2026-08-26
---

## The signal

Settings → Notifications has **no** read/unread DOM attribute. The only distinction is a
theme-token colour driven by `is_seen`:

| Element | Unread | Read (dark theme, 2026-08-26) |
|---|---|---|
| message `<Typography>` (`NotificationListItemMessage.jsx:11`) | `rgb(255,255,255)` | `rgb(169,183,193)` |
| date `<Typography>` (`NotificationTable.jsx:219`) | `rgb(255,255,255)` | `rgb(169,183,193)` |
| in-message `<Link>` | `rgb(41,184,245)` | `rgba(41,184,245,0.7)` |

- `notification-message-text` is the wrapper `<Box>` — its computed colour is the
  inherited default and does NOT change. The colour lives on the inner `<Typography>`.
- Assert the DIFFERENCE (same row before/after, or read row vs unread sibling), never the
  literal rgb — a theme change would break the test while the contract holds.
- Read it with `locator.evaluate("el => window.getComputedStyle(el).color")` — precedent
  `automation/pages/agent_form_page.py:230`. It is an observation, not a substitution;
  declare it when the reviewer's `\.evaluate\(` grep hits.

## Clicking a row does NOT mark it read

Zero `/notifications/notifications/prompt_lib/` requests after a row-message click.
`GridTableRow` has no row-level `onClick`; the message `<Link>` is a plain
`target="_blank"` anchor. Only the toolbar toggle (table) and the sidebar popover's hover
button (`context === 'list'`) transition state. Clarification filed:
elitea-testing-public#1784.

Related: [[test_project_has_no_toolkits_or_credentials]]
