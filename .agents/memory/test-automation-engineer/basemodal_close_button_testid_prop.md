---
name: BaseModal close-button testid prop is closeButtonTestId
description: BaseModal destructures closeButtonTestId; closeButtonDataTestId renders nothing — main itself has this bug in SelectIconDialog
type: reference
aliases: [closeButtonDataTestId, closeButtonTestId, BaseModal testid, dialog close button testid]
tags: [area/eliteaui, type/locator]
created: 2026-08-26
updated: 2026-08-26
---

## The prop name

`src/[fsd]/shared/ui/modal/BaseModal.jsx` (EliteaUI, verified on `origin/main`
2026-08-26) destructures exactly these testid props:

```
'data-testid': dataTestId,   titleTestId,   titleIconTestId (ours only),
closeButtonTestId,           confirmButtonTestId,   cancelButtonTestId
```

and renders `data-testid={closeButtonTestId}` at `BaseModal.jsx:152`.

**`closeButtonDataTestId` is NOT a real prop.** Passing it renders no attribute at
all — the close button silently gets `data-testid={undefined}` and every locator
bound to it fails. This matches canon (`.agents/testing.md` § Locator policy: the
prop is `testId`/`<part>TestId`, never a `data`-prefixed name).

## Known live instance of the bug on main

`src/components/SelectIconDialog.jsx` on `origin/main` passes
`closeButtonDataTestId="agent-icon-picker-close-button"` — dead on main, so that
testid does not exist on any deployed env even though the string is present in the
source. Our `automation/testids` branch carries the corrected `closeButtonTestId`
form (kept through the 2026-08-26 sync merge, commit b57bb62d).

Consequence: a grep-based promotability check that only looks for the testid
*string* will report this one as "on main" when it is functionally absent. Check
the prop NAME, not just the value.

Related: [[project_briefing]]
