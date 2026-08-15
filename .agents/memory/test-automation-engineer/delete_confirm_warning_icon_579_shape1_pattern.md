---
name: delete_confirm_warning_icon_579_shape1_pattern
description: CORRECTED (fix round 1) — delete-confirm warning icon is NOT a #579 exception; it's a real testid now
type: feedback
---

**Correction (ELITEA-2193 fix round 1):** the original version of this entry
(and the merged code it described) misclassified `DeleteEntityModal`'s
title-icon `<svg>` as a **#579-shape-1 sanctioned exception**
("third-party MUI internal node, no app testid placeable"). That was **wrong**
— reviewer-caught, verified false against EliteaUI source:

- The icon component (`ModalConstants.MODAL_ICONS[typeIcon]`, e.g.
  `WarningIcon`) is a **first-party** SVG asset imported via
  `@/assets/attention-icon.svg?react` — our own app JSX render output, not a
  third-party library's internal DOM (unlike ReactFlow's `rf__wrapper` or
  CodeMirror's per-line nodes, the two genuine #579 shapes).
- It renders inside `src/[fsd]/shared/ui/modal/BaseModal.jsx`'s
  `renderIconType()` — a shared component **we own**, in the exact same
  title `Box` that already threads explicit testid props to every sibling
  element (`titleTestId`, `closeButtonTestId`, `cancelButtonTestId`,
  `confirmButtonTestId`). The icon was simply the one element in that group
  nobody had wired a prop for yet.
- Per `.agents/testing.md` § Locator policy: "Missing testid on the target?
  That is work to do, not a reason to rung down." A #579 exception requires
  the testid to be genuinely unplaceable — it wasn't.

**Do not cite the merged `DELETE_DIALOG_BACKDROP` (ELITEA-2116,
`.MuiBackdrop-root`) as precedent for this shape** — that one IS a genuine
#579 exception (MUI's own `Dialog` backdrop chrome, no app JSX involved).
Citing an unrelated merged exception as authority for a different element is
exactly the "precedent is not authority" anti-pattern
(`.agents/role-overrides.md`).

**The fix (now in place):** `BaseModal` gained a new optional
`titleIconTestId` prop (same channel/shape as the four existing testid
props), wired `data-testid={titleIconTestId}` on the `<Icon>` element.
`DeleteEntityModal` passes `titleIconTestId="delete-confirm-title-icon"`
alongside its existing `titleTestId="delete-confirm-title"`
(`EliteaAI/EliteaUI@7b359d32` on `automation/testids`). Purely additive — no
new DOM node, no hook change; other `BaseModal` callers don't pass the prop
and keep byte-identical DOM.

`ChatPage` now has a real `delete_confirm_title_icon = LocatorDescriptor(testid="delete-confirm-title-icon")`
field; `get_delete_confirm_title_icon()` just waits on it — no scoped raw
`svg` selector, no `DELETE_CONFIRM_TITLE_ICON` constant (removed).

Test still asserts (page objects don't own assertions):

```python
warning_icon = chat.get_delete_confirm_title_icon(timeout=UI_ELEMENT_TIMEOUT)
expect(warning_icon).to_have_css("fill", "rgb(233, 121, 18)")
```

**Lesson for next time a "#579 exception" is reached for:** before writing
the exception comment, actually open the component the raw handle lives in
and check (a) is it under a path EliteaUI doesn't own / is it genuinely a
third-party library's internal render tree, and (b) does the immediate
parent already thread sibling testid props that the target element was
simply left out of — (b) is a strong signal the exception doesn't apply and
`add-data-testid` should be run instead.

Unrelated, still valid: live-verified accessible name for the SAME dialog's
trigger button — hovering a non-owner row's delete icon
(`ChatPage.hover_participant_user_row()`) exposes accessible name exactly
`"Remove user"` (`DeleteParticipantButton.jsx`'s
`removeLabel = 'Remove ' + (entityType || 'participant')`, `entityType`
resolved to `'user'`). `expect(button).to_have_accessible_name("Remove user")`
— no new testid needed.
