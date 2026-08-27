---
name: Adding a testid to single-line JSX trips the zero-functional-impact grep
description: EliteaUI's prettier sets singleAttributePerLine, so a one-line JSX element reflows to 4 lines the moment a testid lands — declare it or the reviewer blocks.
type: feedback
aliases: [singleAttributePerLine, prettier reflow testid, step 5.5 grep false hit, zero-functional-impact grep]
tags: [area/testids, area/review]
created: 2026-08-27
updated: 2026-08-27
---

## The trap

`EliteaUI/.prettierrc` sets `"singleAttributePerLine": true`. So a JSX element written
on one line — `<Box sx={styles.root}>` — **must** become

```jsx
<Box
  sx={styles.root}
  data-testid="..."
>
```

the moment a second attribute is added. The commit hook runs prettier, so there is no
way to keep it on one line.

## Why it matters

The reviewer's mandated Step-5.5 zero-functional-impact greps
(`.agents/role-overrides.md` § Reviewer slot) then report two hits that look like real
findings but are the SAME pre-existing element:

- `git diff … | grep -nE '^-' | grep -vE 'testid|TestId'` → `-    <Box sx={styles.root}>`
- `git diff … | grep -nE '^\+.*<(Box|div|span|Fragment)'` → `+    <Box`

No DOM node was added, no element replaced, no hook moved.

## What to do

**Declare it in the testid commit body** — name the reflow, name `singleAttributePerLine`,
and state that the `-` line and the `+ <Box` are the same element. An undeclared hit is a
violation (§ Declared-improvisation protocol); a declared one costs the reviewer ten
seconds. Worked example: EliteaAI/EliteaUI@efda0603 (ELITEA-2291, SettingsPreview.jsx).

Elements already spanning multiple lines (`IconButton`, `Typography`, `Field.*` with 2+
props) take a pure `+` line and produce no hit at all — this only bites single-line targets.

Related: [[afs_on_main_provenance_claim_needs_two_ref_grep]]
