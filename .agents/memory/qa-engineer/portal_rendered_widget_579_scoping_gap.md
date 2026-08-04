---
name: Portal-rendered third-party widget — #579 scoping gap
description: antd/react-js-cron dropdowns portal to <body>, can't be DOM-scoped to a testid'd parent — the #579 discipline has no shape for this
type: feedback
---

`.agents/testing.md` § Stop+flag rule (#579) requires any sanctioned raw-handle
exception to be scoped to a real app testid'd parent: `self.testid_parent.locator(...)`,
never a free-floating page-level handle. That works for elements that render as real
DOM descendants of their container (e.g. `SCHEDULE_CRON_SELECT = ".react-js-cron-select"`
chained off `schedule_modal`).

It does NOT work for a widget whose dropdown **portals to `document.body`** — antd's
`Select` (used by `react-js-cron`'s Every/on/hour/minute pickers in the Schedule
settings modal) is exactly this: the open dropdown (`.ant-select-dropdown`) is not a
DOM descendant of the modal that triggered it, so `schedule_modal.locator(...)` can
never find it. `CRON_DROPDOWN` in `pipeline_detail_page.py` ended up as
`self.page.locator(".ant-select-dropdown:visible")` — a genuinely page-level handle,
justified only by "one such dropdown is ever open at a time" (a test-structure
invariant, not a DOM-scoping one).

Found during PR #1141 review (ELITEA-2007). Flagged as a real canon gap requiring
declaration in the PR description per role-overrides.md § Declared-improvisation
protocol, not something to silently ship via an inline code comment alone. If this
recurs on another portal-rendered library (MUI `Popper`/`Menu` also portal, though
those usually get `MuiPopper-root`/`MuiMenu-root` wrapper testids more easily since
the app owns the trigger), the same reasoning applies: name the portal constraint
explicitly, don't just scope-and-hope.
