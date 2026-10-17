---
name: generated-entity-chip requires hover before click (chat-created-entity flows)
description: The in-chat "entity created" chip (Agent/Pipeline/Toolkit/Skill/Project-Context "Build with AI"/create-via-chat) has no onClick on its own container — a bare .click() silently no-ops. Hover first to reveal "Open entity"/"Delete entity" buttons, click one of those.
type: feedback
---

## The component

`GeneratedEntityChip.jsx` (`data-testid="generated-entity-chip"`) renders in
every chat response that created an Agent/Pipeline/Toolkit/Skill/Project
Context via the in-chat "Build with AI"/create-via-chat flows
(`ApplicationAnswer.jsx`'s `created_entities` array). It is ONE shared
component across all five entity types — only the label text and icon
differ.

## The gotcha, confirmed live (ELITEA-3368 session, 2026-10-17)

The chip's main `Box` container has **no `onClick` handler at all** — a
plain `page.locator('[data-testid="generated-entity-chip"]').click()` is a
silent no-op (no navigation, no error, nothing happens — easy to mistake
for a timing issue and retry/wait longer, which also does nothing).

The real affordance is on two CHILD buttons that only render once the chip
is **hovered** (`isHovering` state, `onMouseEnter`/`onMouseLeave` on the
container):

- `role="button" name="Open entity"` — calls `onEntityCreated?.(entity,
  true)`, which opens the entity's editor/Canvas. This is almost always
  what a test wants.
- `role="button" name="Delete entity"` — opens a confirm-delete modal
  (`Modal.DeleteEntityModal`), only rendered at all when `onDeleteEntity` is
  wired for that caller.

Neither button carries a `data-testid` as of this session — both are
`role=`+`name=` rung (2), `suggested_testid=`:
`generated-entity-chip-open-button` / `generated-entity-chip-delete-button`.

## The fix

```python
chip = self.page.locator('[data-testid="generated-entity-chip"]')
chip.hover()
chip.get_by_role("button", name="Open entity").click()
```

Also: the chip only renders once `!isStreaming && !isLoading`
(`ApplicationAnswer.jsx`) — wait for the chip itself to be visible before
hovering, don't assume it's present the instant the response text appears.

## Where this applies

Any case driving an in-chat "create via chat"/"Build with AI" flow for
Agent, Pipeline, Toolkit, Skill, or Project Context — all five share this
exact component and gotcha. First hit and fully root-caused during
ELITEA-3368 (Project Context); worth checking for on any of the other four
entity types' own chip-click steps if a case ever asserts on it directly
(most existing specs for Agent/Pipeline reach the editor via the creation
button's own post-save transition, not by clicking the response chip
afterward, so this may not have been hit yet elsewhere — verify live before
assuming an existing test already handles it).
