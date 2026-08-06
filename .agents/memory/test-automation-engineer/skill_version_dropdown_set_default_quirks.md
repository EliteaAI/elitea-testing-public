---
name: Skill VERSION dropdown set-default control quirks (implementer)
description: version.helpers.jsx's buildVersionOption() renders the pin icon AND the hover-revealed set-default control as descendants of the SAME version-option-{name} MenuItem (via SingleSelectMenuItem's ListItemIcon{option.icon}) — so both scope cleanly under VERSION_OPTION; the set-default Box's only pre-existing handle was a non-unique CSS #show-on-hover id used purely for the :hover CSS-selector reveal, not a locator
type: feedback
---

## Context

ELITEA-2437 ("Version dropdown shows pin/set-as-default button and
confirmation message" — the per-VERSION default-setting control, distinct
from ELITEA-2435's list-level "pin to top"). `SkillDetailPage` gained a
set-default surface mirroring `AgentDetailPage`'s already-shipped ELITEA-1891
VERSION-selector pattern almost exactly.

## Load-bearing findings

1. **Both `version-option-pin-icon` and the set-default control render
   inside the SAME `version-option-{name}` MenuItem.**
   `buildVersionOption()` (`version.helpers.jsx`) returns `{ icon:
   <IconBlock/>, testId: version-option-${name}, ... }`; the consumer
   (`SingleSelectMenuItem.jsx`) renders `option.icon` inside a
   `<ListItemIcon>` that is a child of the `<MenuItem
   data-testid={option.testId}>`. So `VERSION_OPTION.format(name)` scopes
   BOTH the pin icon and the set-default control cleanly — no separate
   page-wide lookup needed, no menu-portal gotcha (unlike the *Agent-skill*
   `SkillVersionSelector.jsx` rework, which portals to `document.body` —
   different component, don't conflate).

2. **The set-default `<Box id="show-on-hover">` had ZERO real locator before
   this case** — its only attribute was a non-unique CSS `id` consumed
   purely by a sibling CSS rule (`'&:hover #show-on-hover': { display:
   'flex' }'` on the parent `MenuItem`'s `sx`) to reveal it on hover. That id
   is NOT a valid locator (non-unique across rows, no `data-testid`) — a
   genuine confirmed-live gap, not a case of "the analyst missed an existing
   testid". Fix: name-keyed `data-testid={`version-option-set-default-${name}`}`
   on the same Box, mirroring the sibling `version-option-{name}` naming
   already used one call up.

3. **`SetDefaultVersionDialog.jsx` already accepted `confirmButtonTestId`**
   (forwarded straight to the confirm `Button.BaseBtn`) — only the *Skill*
   flow's call site (`EditSkill.jsx:271`) never passed it. The *Agent* flow
   (`useSetDefaultVersion.hooks.jsx:104`) already wires
   `confirmButtonTestId="agent-set-default-version-confirm-button"`, so this
   was a pure one-line precedent copy, not new plumbing — always check a
   dialog's existing props/JSDoc before assuming a testid needs threading
   from scratch.

4. **Hover-reveal needs a real wait, not just `.hover()`** — the CSS
   transition (parent-`:hover` selector) needs ~300ms to actually flip
   `display: none` -> `flex` before the child locator's `wait_for(state=
   "visible")` will find it. Same idiom as every other hover-gated control
   in this suite (`.claude/rules/mui-patterns.md` § Hover-Dependent
   Elements) — nothing new, just confirming it applies here too.

5. **`get_version_option_order()` / `VERSION_OPTION_ANY` needed BOTH nested
   testid prefixes excluded**, not just the pin icon (unlike
   `AgentDetailPage`'s ELITEA-1891 version, which only had the pin icon to
   exclude): `[data-testid^="version-option-"]:not([data-testid="version-
   option-pin-icon"]):not([data-testid^="version-option-set-default-"])` —
   the new set-default testid ALSO starts with the `version-option-` prefix
   and would otherwise be mistaken for an option row when reading dropdown
   order.

## Where

- `automation/pages/skill_detail_page.py` — search "ELITEA-2437" in the
  file for the version-management block additions.
- `automation/tests/ui/skills/test_skill_version_set_default.py`.
- EliteaUI: `src/[fsd]/entities/version/lib/helpers/version.helpers.jsx`
  (set-default testid), `src/[fsd]/pages/skills/EditSkill.jsx`
  (`confirmButtonTestId` wiring) — both on `automation/testids`,
  `EliteaAI/EliteaUI@4a8c979f`.
