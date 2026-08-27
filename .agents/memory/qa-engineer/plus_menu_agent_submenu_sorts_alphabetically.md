---
name: Plus-menu agent submenu sorts alphabetically, not by recency
description: Chat plus-menu → Agents list is client-side alphabetised, so ".first" is NOT the newest agent
type: reference
aliases: [add_agent_participant, plus menu agents, agent participant first, useFilteredEntityItems]
tags: [area/chat, type/gotcha]
created: 2026-08-27
updated: 2026-08-27
---

## What

`ChatPage.add_agent_participant(prefix)` selects
`li[role="menuitem"]:has-text("<prefix>")`**.first** from the chat plus-menu → Agents submenu.
That is **not** the agent the test just created.

## Why

`../EliteaUI/src/hooks/chat/useFilteredEntityItems.js` post-processes the server rows:

```js
const sortEntityItemsByPublicStatus = (a, b) => {
  if (a.isPublic !== b.isPublic) return a.isPublic ? 1 : -1;
  return a.label.localeCompare(b.label);          // ALPHABETICAL
};
const filterItemsBySearch = search => item =>
  item.label && item.label.toLowerCase().includes(search.toLowerCase());
```

The API is called with `sort_by=created_at&sort_order=desc` (`useDropdownData.jsx`), but the
client re-sorts: private agents first, then public, **each block alphabetically by name**.
Equal names tie → V8 stable sort preserves the server's recency order (why a same-name
duplicate probe looked "newest-first" and hid the bug).

The client filter is a **literal** substring match, so it also drops rows the server returned via
SQL `LIKE` (where `_` is a single-char wildcard: `query=autotest_` returns
`autotest GH PR Reviewer`, but it never renders).

## Consequence for tests

Any leftover agent whose name literally contains the prefix and sorts earlier wins. Real example
in project 399: `autotest_test_add_toolkit_to_age` (sibling test's leaked agent) sorts before
`autotest_test_agent_with_toolkit` (`test_ad` < `test_ag`), so the wrong agent — no toolkit, its
own model — is added as participant.

**Use `add_agent_participant_by_id(project_id, agent_id)`** (testid
`agents-menu-item-agent-{project_id}-{agent_id}`) whenever the test created the agent and knows
its id. Name-prefix selection is only safe if the name is globally unique in the project.

Also: the search input fires **one request per keystroke, no debounce**; at 500 ms after typing
the submenu can still read "Loading...".

Verified live 2026-08-27 against localhost:5173 / project 399 (decoy-agent experiment, #1814).
