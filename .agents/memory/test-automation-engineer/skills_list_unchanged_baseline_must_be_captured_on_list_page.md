---
name: Skills-list "unchanged" baseline must be captured on the list page
description: get_skill_card_names() called while still on /skills/create returns [] — capture names_before via list_page.navigate() first
type: feedback
---

ELITEA-1997 (build-with-ai cancel-from-prompt-step): the "Skills list is
unchanged after Cancel" check needs a real `names_before` snapshot. Calling
`SkillsListPage.get_skill_card_names()` right after `navigate_to_create()`
(i.e. while still on `/skills/create`) silently returns `[]` — the method
just reads whatever `entity_card_name` locators are on the current DOM, it
does not assert you're on `/skills/all`. First run passed the assertion
for the wrong reason until `names_after` came back non-empty and the
equality failed against a bogus `[]` baseline.

Fix: `list_page.navigate()` (to `/skills/all`) to capture `names_before`,
**then** `list_page.navigate_to_create()` to proceed with the flow. Same
shape applies to `AgentsListPage.get_agent_card_names()` and any other
list page's "verify the list is unchanged" pattern — always capture the
baseline while actually on the list route, not the route you're about to
leave.
