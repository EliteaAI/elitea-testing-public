---
name: Testid prefix enumeration can match a child icon inside the option
description: '[data-testid^="select-option-"] also matches the ✓ icon INSIDE the selected MenuItem — enumeration yields a spurious empty entry; read per value.'
type: feedback
aliases: [select-option-selected-icon, SELECT_OPTION_PREFIX, spurious empty option, "#1806"]
tags: [area/locators, type/gotcha]
created: 2026-08-26
updated: 2026-08-26
---

## What happened

`PipelineDetailPage.SELECT_OPTION_PREFIX = '[data-testid^="select-option-"]'` enumerates the
options of an open MUI listbox. EliteaAI/EliteaUI@b0a7d61a added
`data-testid="select-option-selected-icon"` to the ✓ `ListItemIcon` **inside** the currently
selected `MenuItem` — which the prefix matches. `get_open_listbox_option_names()` therefore
returns a spurious empty string for whichever option is selected:

```
['Chat Message', '', 'Schedule', 'Webhook']
```

Tracked as issue #1806. The icon testid is on `automation/testids` only, so today this is a
**localhost-only** red: the same spec is green on dev.elitea.ai. It flips to a suite-wide DEV
red the moment a human cherry-picks that commit.

## The lesson

A prefix/family testid selector is only safe while nothing NESTED under a matching element
also carries a testid in the same namespace. That is not a property you control — a UI-side
commit can break every caller at once, and it breaks them **asymmetrically across
environments**, which reads as flake.

**Prefer per-value handles** (`SELECT_OPTION.format(value)`) whenever the values are known.
They assert the same thing, and they are immune. Reserve family enumeration for the genuine
"I don't know the values up front" case.

Corollary for triage: a spec that fails on localhost but passes on DEV (or vice versa) is a
**provenance** question first — diff `origin/main` against `origin/automation/testids` for the
component before suspecting the test.

Related: [[aria_disabled_is_absent_not_false_when_enabled]]
