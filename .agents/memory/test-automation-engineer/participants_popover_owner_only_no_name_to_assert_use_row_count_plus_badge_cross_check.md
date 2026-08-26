---
name: Owner-only participants popover has no known name to assert — use row-count + badge cross-check
description: When a conversation's Users popover has only the owner (no invited-by-name second participant), assert PARTICIPANT_ROW_PREFIX row count vs get_participants_badge_count instead of a name substring.
type: feedback
---

## Pattern

Sibling tests that assert real participant content in the Users popover
(`test_team_users_mention_and_remove_participants.py`, ELITEA-2168) know a
specific invited user's display name ahead of time and assert
`name in popper_text`. That idiom doesn't apply when the conversation under
test only ever has the OWNER as a participant (no `open_add_users_modal()` /
`search_and_select_add_user()` invite step) — the owner's display name isn't
wired into test constants/settings, so there's no known string to assert.

## Fix used (ELITEA-2188, PR #1562, fix round 1)

Assert the DYNAMIC row list directly instead of a name:

```python
badge_count = chat.get_participants_badge_count(section="users", timeout=UI_ELEMENT_TIMEOUT)
popper = chat.open_participants_popover(section="users", timeout=UI_ELEMENT_TIMEOUT)
participant_rows = popper.locator(chat.PARTICIPANT_ROW_PREFIX)  # '[data-testid^="chat-participant-row-"]'
participant_rows.first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
row_count = participant_rows.count()
assert row_count >= 1, "..."
assert str(row_count) == badge_count, "..."  # two independent renders must agree
```

`PARTICIPANT_ROW_PREFIX` and `get_participants_badge_count()` both
pre-existed on `ChatPage` (ELITEA-1793/2167 work) — no page-object change
needed, purely additive to the test. The badge count is CSS-generated
content (`::after`), a completely separate render path from the popper's row
list, so agreement between the two is a real cross-check, not a tautology.

Fixes the vacuous-heading-text finding documented in
`.agents/memory/qa-engineer/static_section_heading_text_independent_of_list_content.md`
for the owner-only case specifically (that entry's suggested fix — assert a
specific participant name — doesn't apply when there's no known name).
