---
name: AFS "on-main ✓" provenance rows need a file-level check, not the two-stage grep
description: The closure-record FILTER silently drops attribute-only lines; whole components can carry zero testids on main
type: feedback
aliases: [provenance, on-main, closure record grep, testid promotability, settings-drawer testids]
tags: [area/review, type/gotcha]
created: 2026-08-28
updated: 2026-08-28
---

## What happened

Re-reviewing PR #1911 (settings-w05, ELITEA-2348/2349) I ran the closure-record
provenance loop from `.agents/workflow.md` § Closure record over the AFS handle rows:

```bash
FILTER='(data-testid|testid[[:space:]]*[:=])'
git grep -- "$t" origin/main -- src/ | grep -qiE "$FILTER"
```

It produced **both** error directions in one pass:

- **False negative** on `data-severity` — the line is `data-severity={severity}` on
  `Toast.jsx:61`, right under `data-testid="toast-alert"`, but the *line itself* carries
  neither `data-testid` nor `testid[:=]`, so stage 2 drops it. The AFS's claim was
  correct and my filter said "not on main".
- **True negative that the AFS got wrong** — `settings-drawer-menu`,
  `settings-nav-item-*` and `SETTINGS_NAV_ITEMS_IN_MENU` were all marked **on-main ✓**.
  `SettingsDrawer.jsx` on `origin/main` contains **zero** occurrences of `testid`
  (case-insensitive); every one of those testids exists only on `automation/testids`.

## The rule

**Verify a provenance row by looking at the COMPONENT FILE on `main`, not by pushing
the testid string through the two-stage filter.**

```bash
cd ../EliteaUI && git fetch origin
git show origin/main:<component path> | grep -niE 'testid'      # does main have ANY?
git diff --stat origin/main origin/automation/testids -- <component path>
```

A file that differs between the two refs is the honest signal. Bare-substring stage 1
cannot see runtime-composed testids at all (`project-selector-trigger` is on main;
the automation locator is `project-selector-trigger-combobox`, composed by the shared
select), and stage 2 cannot see state attributes that sit on their own line.

## Why it matters

A wrong `on-main ✓` row is inherited by the lead's closure record and turns into a false
"promotable" claim — the exact `#19` failure the fresh-fetch rule exists to prevent. It
also hides the real status: a case whose handles are `automation/testids`-only is green
on localhost and **red on any deployed env** until a human cherry-picks.

Related: [[secrets_page_object_duplicate_class_member_shadows_silently]]
