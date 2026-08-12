---
name: Skill Tags field rejects hyphens; chip delete only via icon, not chip body
description: Skill Tags combobox silently drops hyphenated freeSolo values (regex is \w+comma+whitespace only); tag chip's onDelete fires only on the delete-icon child, not the chip label/body — confirmed live by direct comparison.
type: feedback
---

Discovered while analysing ELITEA-2433/2434 (Skill tag add/save/remove,
localhost:5173):

- **Tags field character set is `[\w,\s]` only — NO hyphens.**
  `TagEditor.jsx` → `AutoCompleteDropDown.jsx` validates freeSolo input
  against `NormalTagNameInputRegExp = /^[\w,\s]+$/g` and, decisively,
  `onChangeMulti` filters the committed value against
  `NormalSingleTagNameInputRegExp = /^[ \t]*[\w]*[ \t]*$/g`
  (`EliteaUI/src/common/constants.js:92-93`) before adding it to the tag
  list. Typing a hyphenated value (e.g. `regression-v1`) and pressing
  Enter clears the input but adds NO chip — zero network calls, 100%
  silent client-side filter. Underscore works fine
  (`regression_v1`). Opposite direction from the Skill *Name* field
  (which REQUIRES kebab-case/hyphens, rejects underscores/spaces) — don't
  assume the two fields share a character-set convention. Filed as
  clarification: `EliteaAI/elitea-testing-public#1445` (case ELITEA-2433's
  literal test data `"regression-v1"` can never be entered).
- **A committed tag chip's delete ("x") icon is the ONLY clickable
  target for removal — clicking the chip's label/body does nothing.**
  Confirmed live by direct comparison: clicking the chip button's center
  (label text area, away from the icon's bounding box) left the tag
  intact and Save stayed disabled; clicking the icon `<img>`/SVG child
  removed it and dirtied the form. MUI's `Chip.onDelete` wires only to
  the `deleteIcon` sub-element. The delete icon itself has **no
  `data-testid`** — `AutoCompleteDropDown.jsx`'s `renderValue()` supports
  a `chipDeleteTestId` prop (function or string, same shape as
  `chipTestId`/`getOptionTestId`) but `CreateSkillForm.jsx`'s
  `<TagEditor>` call site never passes it. Fix: add
  `chipDeleteTestId={option => \`skill-tag-chip-delete-${option?.name}\`}`
  at that call site (one-line, mirrors the existing `getOptionTestId`
  pattern) — 100% app-owned JSX, not a `#579` exception. Interim
  locator: scope `skill-tag-chip` by text, then click its only child
  (icon).
- Full AFS: `test-specs/skills/l3_add-save-remove-skill-tag_ELITEA-2433.md`,
  `test-specs/skills/l3_multiple-tags-persist-on-creation-and-edit_ELITEA-2434.md`.
  Surface digest updated: `test-specs/skills/_surface.md` § Tags —
  add/remove on an existing Skill.
