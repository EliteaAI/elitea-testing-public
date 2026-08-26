---
name: MUI Dialog testid — paper vs Modal root
description: A data-testid on <Dialog> lands on the full-viewport Modal root, making any "is it fullscreen" box assertion a tautology; wire it on slotProps.paper.
type: feedback
aliases: [dialog fullscreen assertion, slotProps.paper testid, MuiDialog-paperFullScreen, fullscreen bounding box]
tags: [area/ui, type/gotcha]
created: 2026-08-24
updated: 2026-08-24
---

## The trap

MUI spreads props passed to `<Dialog>` onto the **Modal root**, which is
`position: fixed; inset: 0` for *every* dialog — fullscreen or not. So a testid
placed there, then asserted with `bounding_box() == viewport`, **passes even if
`fullScreen` is removed from the component**. It is a tautology dressed as an
assertion.

## The fix

Wire the testid on the dialog **paper**, which is the element MUI actually
resizes for `fullScreen` (and the one carrying `role="dialog"`):

```jsx
const tourDialogSlotProps = {
  paper: {
    'data-testid': 'onboarding-tour-fullscreen-dialog',
    sx: styles.tourDialogPaper,
  },
};
<Dialog fullScreen open={open} slotProps={tourDialogSlotProps}>
```

Descendant scoping (`'[data-testid="…dialog"] [data-testid="…"]'`) is unaffected:
the header, `DialogContent` and its children are all inside the paper.

Shipped in EliteaAI/EliteaUI@3ba7967d for ELITEA-2236.

Related: [[headed_mode_viewport_size_is_none]]
