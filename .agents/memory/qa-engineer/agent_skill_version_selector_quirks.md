---
name: Agent skill version-selector quirks
description: Attached-skill card's version-selector control IS functional via mouse click but has no ARIA role/testid/tabIndex; accessibility-snapshot ref-based clicks silently resolve to the wrong ancestor and no-op — must use a CSS-class-scoped locator (.version-text) instead
type: feedback
---

Discovered while analysing ELITEA-1789 (Attach a Skill to an Agent and verify it
appears with version selector, localhost:5173):

- **The version-selector control on an attached-skill card (agent detail page,
  Skills accordion) IS real and functional** — clicking it opens a "Versions"
  popper menu (header "Versions", menuitem = version name, e.g. "base"). Confirmed
  live, reproducibly.
- **But it has zero accessibility semantics**: the actual clickable wrapper
  (`div.MuiBox-root` containing `span.version-text` + a `KeyboardArrowDownIcon`
  chevron svg) has `tabIndex="-1"`, `role=null`, `aria-label=null`,
  `data-testid=null`. Not keyboard-reachable, not identifiable to a screen reader,
  no automation handle. Filed as
  github.com/EliteaAI/elitea-testing-public/issues/46 (MINOR, isolated,
  non-blocking).
- **Load-bearing automation gotcha**: clicking via a Playwright accessibility-
  snapshot `ref=` (i.e. any ARIA-tree/role-based locator, which is how
  `browser_click(target=ref)` resolves) for the visible "base" text silently
  resolves to a *different, non-interactive ancestor* one level further up
  (`cursor: default`, not the real `cursor: pointer` wrapper) and does **nothing**
  — no error, no menu, just silently clicks the wrong element. Confirmed
  reproducibly (2/2 attempts). Only a CSS-class-scoped locator
  (`page.locator('.version-text')`, scoped further to the specific skill's card
  via an ancestor `has_text` filter when multiple skills are attached) or a raw
  coordinate click reliably opens the menu.
- **Practical rule**: when a MUI `Box`-based custom control has a `cursor: pointer`
  style but no semantic role, do NOT trust `browser_snapshot`'s ref-to-locator
  resolution for it — verify with a direct CSS-class or JS-evaluate click first,
  then find the equivalent real Playwright locator (CSS class, not role/testid,
  since none exist) before writing the AFS handle.
- Attachment is still auto-saved immediately via `PATCH
  .../skill/prompt_lib/{project}/{skill-id}` → `201`, same as ELITEA-1735; the
  agent-level Save button stays disabled throughout — "Save the Agent" in a case
  script should be verified via full-page-reload persistence, not a literal Save
  click.
- Full AFS: `test-specs/skills/l3_attach-skill-to-agent-with-version-selector_ELITEA-1789.md`.
