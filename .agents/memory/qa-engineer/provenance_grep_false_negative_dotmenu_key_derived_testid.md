---
name: Provenance grep false-negative — DotMenu testids derived from a `key:` field
description: A dot-menu item's testid is built by DotMenu from a `key:` field, so its source line contains no "testid" at all and the closure-record stage-2 filter drops it
type: feedback
aliases: [bucket-menu-rename-menuitem not found, DotMenu key testid, menuitem testid provenance, closure record false negative]
tags: [area/testids, type/gotcha]
created: 2026-08-23
updated: 2026-08-23
---

## The trap

`DotMenu.jsx` derives each item's `data-testid` as `` `${item.key}-menuitem` `` from
the `key` field of the `menuItems` array. So the *only* line in EliteaUI source that
mentions the testid is:

```jsx
// src/pages/Artifacts/Components/BucketItem.jsx:165
{
  key: 'bucket-menu-rename',      // -> data-testid="bucket-menu-rename-menuitem"
  label: 'Rename',
```

`.agents/workflow.md` § Closure record's stage-2 filter is
`grep -iE '(data-testid|testid[[:space:]]*[:=])'`. That line carries **neither**
`data-testid` **nor** `testid` in any case form — so a testid that IS present on
`automation/testids` is reported `no`. Verified 2026-08-23 on ELITEA-1810:
`bucket-menu-rename` greped `main:no testids:no`, while
`git grep bucket-menu-rename origin/automation/testids -- src/` returns the line and
EliteaAI/EliteaUI@c91c2aac added it.

This is a THIRD shape beyond the two already recorded
([[provenance_grep_false_negative_multiline_testid_prop]] and
[[provenance_grep_needs_case_insensitive]]): here the derivation happens in the
shared component, not at the call site.

## What to do

For any `*-menuitem` testid, strip the `-menuitem` suffix and grep the **key**:

```bash
git grep -n "key: '<testid-minus-menuitem>'" origin/automation/testids -- src/
git grep -n "key: '<testid-minus-menuitem>'" origin/main -- src/
```

Read the hits; do not run them through the stage-2 filter. Same applies to any
shared component that composes a testid from a non-testid-named prop.

Related: [[provenance_grep_false_negative_multiline_testid_prop]] · [[provenance_grep_needs_case_insensitive]]
