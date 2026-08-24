---
name: Sidebar notifications popover can render empty while the unread count says >0
description: The bell popover's list is a separate fetch from the unread-count response; under load it can still be empty when a 5s expect fires.
type: project
aliases: [notifications popover, mark all as read, sidebar-notifications-mark-all-read-button, ELITEA-2234]
tags: [area/onboarding, area/sidebar, type/flake-candidate]
created: 2026-08-24
updated: 2026-08-24
---

## Observation (batch onboarding-w4 hardening gate, 2026-08-24)

`tests/ui/onboarding/test_sidebar_notification_badge.py` (ELITEA-2234) passed
2 consecutive gate runs (34.3s, 32.8s) and failed the 3rd (56.9s, ~1.7x slower):

```
tests/ui/onboarding/test_sidebar_notification_badge.py:153:
    expect(sidebar.notifications_mark_all_read_button).to_be_visible()
E   Error: element(s) not found
E     - Expect "to_be_visible" with timeout 5000ms
E     - waiting for get_by_test_id("sidebar-notifications-mark-all-read-button")
E   Aria snapshot:
E   - text: Notifications
E   - button "Close notifications"
E   - button "View all"
```

The popover WAS open (title + Close + View all present); only the notification
rows — and therefore "Mark all as read", which renders only when
`notifications.length > 0` — were missing. The spec's own precondition
`assert unread_total > 0`, taken from the product's unread-count response,
passed in that same run.

So the unread COUNT and the popover LIST are two different sources. The count
answered >0 while the list rendered empty. Two candidate explanations, not
resolved here: the list's own fetch had not resolved within the assertion's
**default 5s** expect timeout (every other assertion in this spec uses
`UI_ELEMENT_TIMEOUT = 10_000`; this one does not), or the two sources genuinely
disagree. Classification is the lead's call.

Note the test does NOT mark anything read (open + close only), so this is not
self-poisoning across runs.

Related: [[onboarding_welcome_card_flake_in_combined_run]]
