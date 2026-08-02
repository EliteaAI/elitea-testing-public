---
name: EliteaUI testid can be derived from a menu item's key, not a literal string
description: some menu-item testids are constructed as `${item.key}-menuitem` at render time — a literal-string grep gives a false "missing" verdict
type: feedback
---

While verifying testid provenance for a closure record (`approved-top10`
batch, ELITEA-1890/1891, `set-as-a-default-menuitem`), a plain
`git grep -- "set-as-a-default-menuitem"` against both `origin/main` and
`origin/automation/testids` in EliteaUI came back empty on both — looking
like a genuinely missing testid, even though the batch's own test
(`test_agent_version_selector_order.py`) exercised that exact locator and
passed clean 3/3 in the lead's own gate runs. Live evidence beat the static
grep.

Root cause: `src/components/DotMenu.jsx`'s generic menu-item renderer builds
`testId: item.key` for every item in its `.map()` (when the item object
itself carries no explicit `testId` field), then `BasicMenuItem` renders
`data-testid={testId ? \`${testId}-menuitem\` : undefined}`. So a menu item
with `key: 'set-as-a-default'` (in
`src/[fsd]/entities/application-tab-bar/ui/ApplicationControls.jsx`) renders
`data-testid="set-as-a-default-menuitem"` — a real, live, working testid —
with the literal string `"set-as-a-default-menuitem"` never appearing
anywhere in source. A bare `git grep` for the full testid string cannot find
it.

**When a literal-string testid grep comes back empty on BOTH refs but the
test using it passes live: don't conclude the testid is missing.** Trace the
page-object locator's exact string back to (a) the menu/list component that
renders it and (b) whether that component derives `data-testid` from a
`key`/id field rather than an explicit prop. Check for a `testId: item.key`
(or similar) pattern in the rendering component before writing "genuinely
absent" into a closure record or promotability table. This class of testid
also has no single "added in commit X" — it's inherent to the shared
component + the menu-item's pre-existing `key`, so it isn't a new-testid
promotion-pending item in a closure record at all.
