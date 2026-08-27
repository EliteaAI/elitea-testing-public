---
name: Agent Tags field — dynamic chip testid pattern + pre-seed payload shape
description: How to wire per-tag testids on the Agent branch of ApplicationEditForm.jsx's shared TagEditor/AutoCompleteDropDown, and how to pre-seed saved tags via create_agent_full().
type: feedback
---

## What (ELITEA-1878/1879, PR implementing test_add_multiple_tags_persist_after_reload
+ test_remove_tag_from_agent_persists_after_reload)

`ApplicationEditForm.jsx`'s `<TagEditor>` call site is shared between the
Agent and Pipeline forms (`isFromPipeline` ternary). The Pipeline branch
already had static testids (`pipeline-tags-input`/`pipeline-tags-chip`,
ELITEA-2021). The Agent branch had these props `undefined` (canon #511 scope
discipline — no case exercised them yet). ELITEA-1878/1879 wired them:

```jsx
inputTestId={isFromPipeline ? 'pipeline-tags-input' : 'agent-tags-input'}
chipTestId={
  isFromPipeline
    ? 'pipeline-tags-chip'
    : option => `agent-tags-chip-${option.name}`
}
chipDeleteTestId={
  isFromPipeline ? undefined : option => `agent-tags-chip-delete-${option.name}`
}
```

`AutoCompleteDropDown.jsx` already supports `chipTestId`/`chipDeleteTestId`
as **either a static string or a function of the option** — no source change
needed there, purely a threading fix at the call site. Used the function form
for the Agent branch so each committed chip gets its own testid
(`agent-tags-chip-{name}`, `agent-tags-chip-delete-{name}`) — a single static
testid (Pipeline's shape) would leave multiple chips sharing one selector.

Page-object side (`agent_form_page.py`): class-level template constants,
`AGENT_TAGS_CHIP = '[data-testid="agent-tags-chip-{}"]'` +
`AGENT_TAGS_CHIP_DELETE = '[data-testid="agent-tags-chip-delete-{}"]'`, plus
`get_tag_chip(tag_name)` / `get_tag_chip_delete_icon(tag_name)` locator
getters and `add_tag(tag_name)` / `remove_tag(tag_name)` action methods.

**Gotcha avoided:** don't add a `[data-testid^="agent-tags-chip-"]` PREFIX
selector to enumerate "all chips" — `agent-tags-chip-delete-{name}` also
starts with the string `agent-tags-chip-`, so a prefix match conflates the
chip and its own delete icon. To check chip ORDER (Axis-2 "chips render in
the order added" check), compare `bounding_box()['x']` on the two named chip
locators instead — no new selector needed.

**Pre-seeding saved tags** (for a case that needs an agent to already HAVE
tags, e.g. remove-a-tag cases): `create_agent_full()`'s payload —
`payload["versions"][0]["tags"] = [{"name": "some_tag"}, ...]` — confirmed
working shape (matches `test_agent_publish_unpublish_version.py` /
`test_agent_version_selector_order.py` precedent, `[{"name": ...}]`, not a
bare string list).

**Priority marker note:** this AFS's own metadata literally read "Priority:
medium (`l2`)" — texually "medium", filename-prefixed `l2`. Per
`afs_priority_vs_pytest_mark_preflight_check.md`'s general mapping
(`l2`(high)→p1, `l3`(medium)→p2) this looks like a filename/text mismatch in
the AFS itself. Resolved by sibling precedent **within this exact file**:
two other `l2`-prefixed AFS in `test_agent_management.py`
(ELITEA-1881 llm-selector, ELITEA-1885 welcome-message) both used `p2` —
went with `p2` to match the file's own established convention rather than
the general l-number heuristic (which a third `l2` sibling, ELITEA-1874/1875
embedded-chat, contradicts by using `p1`). When AFS priority text and
filename number disagree, check 2-3 siblings in the same file before
picking — don't trust either signal alone.
