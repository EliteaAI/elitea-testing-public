---
name: EliteaUI prettier forces a JSX tag reflow when a testid is added
description: singleAttributePerLine turns a 1-line JSX tag into 3 lines, producing a removal-grep hit that must be declared
type: feedback
aliases: [singleAttributePerLine, prettier reflow, zero-functional-impact grep 3, testid removal hit]
tags: [area/testids, area/elitea-ui]
created: 2026-08-24
updated: 2026-08-24
---

## The fact

`../EliteaUI/.prettierrc` sets `"singleAttributePerLine": true` (and
`printWidth: 110`). So the moment you add a `data-testid` to a JSX tag that
currently has **one** attribute on one line, prettier rewrites it to the
multi-line form — and the repo's `lint-staged` hook runs `prettier --write` on
commit, so you cannot opt out.

```jsx
- <ListItemIcon sx={[styles.menuItemIcon, styles.menuItemSelectedIcon]}>
+ <ListItemIcon
+   data-testid="select-option-selected-icon"
+   sx={[styles.menuItemIcon, styles.menuItemSelectedIcon]}
+ >
```

## Why it matters

That reflow is a hit on the reviewer's third zero-functional-impact grep
(`git diff … -- src/ | grep -nE '^-' | grep -vE 'testid|TestId'`,
`.agents/role-overrides.md` § Reviewer slot) — the removed line contains no
`testid`, so it looks like a functional deletion.

**It is unavoidable, so declare it rather than fight it.** Name it in the testid
commit body as an `add-data-testid` § Mandatory-plumbing exception, say prettier
forced it, and paste `npx prettier --check <file>` passing. An undeclared hit is
a violation; a declared one is fine.

## Related

[[avoid_widening_a_render_prop_callback_to_host_a_testid]]
