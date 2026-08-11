---
name: EntityIcon SVG placeholder + hover-before-click implementer quirks
description: EntityIcon.jsx (agent-form-icon-button / entity-card-icon) renders an inline SVG placeholder with NO <img> element at all until the first icon is explicitly selected — only picker option items (agent-icon-picker-option-{n}) always render <img>. Also confirms the icon avatar's onClick to open SelectIconDialog only fires once its hover-triggered edit-pencil overlay is mounted (hover() before click(), or click twice).
type: feedback
---

## The gotcha (confirmed live, ELITEA-1899 implementer pass)

`EntityIcon.jsx` (used as `agent-form-icon-button` on the detail/edit and create agent
forms, and as `entity-card-icon` on list/dashboard cards — shared across
Agents/Skills/Pipelines/MCPs per `Card.jsx`) renders **two different DOM shapes**
depending on whether an icon has ever been explicitly selected:

- **No icon selected yet** (fresh agent, or any entity that has never had its icon
  changed): renders an inline `<svg>` default-icon glyph directly inside the
  testid container. **There is no `<img>` element at all** — `container.locator("img")`
  returns zero matches and will time out waiting for visibility.
- **After an icon has been selected at least once**: renders an `<img src="...">`
  inside the same testid container.

**Implication for page-object methods reading `img.src` off `agent-form-icon-button`
or `entity-card-icon`:** always handle the "no `<img>` yet" case explicitly (catch
the wait-for-visible timeout and return `""`/`None`) rather than assuming an `<img>`
is always present. `AgentDetailPage.get_header_icon_src()` does this.

Picker **option** items (`agent-icon-picker-option-{index}`,
`agent-icon-picker-default-icon`, `agent-icon-picker-uploaded-{index}`) are NOT
affected — they always render `<img>` regardless of selection state, since they're
just static preset thumbnails in `SelectIconDialog.jsx`.

## Hover-before-click to open the picker (also ELITEA-1899, confirmed 2/2)

The icon avatar (`EntityIcon` with `editable={true}`) only fires its `onClick`
(which opens `SelectIconDialog`) once its hover-triggered `EditIcon` pencil overlay
is already mounted. A single scripted Playwright `.click()` with no prior
`.hover()` lands on the pre-hover DOM node and only triggers the `onMouseEnter`
state — it does NOT open the dialog. A second click (now hovering) does.
`AgentDetailPage.open_icon_picker()` calls `.hover()` immediately before `.click()`.
Real users are unaffected (mouse naturally hovers before a real click). Not a
product defect — documented in the AFS as an automation-only interaction quirk.

## Where this is implemented

`automation/pages/agent_detail_page.py` — `agent_icon_button`, `icon_picker_dialog`,
`open_icon_picker()`, `select_icon_option()`, `get_header_icon_src()`.
`automation/pages/agents_list_page.py` — `entity_card`, `entity_card_icon`,
`get_card_icon_src()`. Test: `automation/tests/ui/agents/test_agent_icon_management.py`.

**Confirmed again on Skills (ELITEA-2428, 2026-08-11):** a skill created via the
live UI form (no icon ever selected) renders zero `<img>` inside `entity-card-icon`
on `/skills/all` — only the generic SVG glyph. `SkillsListPage` therefore does NOT
carry a `get_card_icon_src()`/`entity-card-icon-img` field at all (would be
unreferenced dead code for every case whose fixture is icon-less); it only has
`entity_card_icon` (container) + `card_icon_locator(name)`, asserting container
visibility. Add the img field only when a future Skills case's fixture actually
has a custom icon.
