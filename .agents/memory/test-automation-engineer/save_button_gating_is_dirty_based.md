---
name: Toolkit/MCP create-form Save button is dirty-based, not validity-based
description: Save enables the instant ANY field is touched; never assert "still disabled after a partial fill" — open issue #633
type: reference
aliases: [shouldDisableSave, formik dirty, save button disabled, ELITEA-1924, issue 633]
tags: [area/toolkits, area/mcp, type/product-behaviour]
created: 2026-08-24
updated: 2026-08-24
---

## The mechanism

`src/pages/Toolkits/CreateToolkitToolTabBar.jsx:43-45`:

```js
const shouldDisableSave = useMemo(() => {
  return isLoading || !formik?.dirty;
}, [isLoading, formik?.dirty]);
```

It never consults required-field validity, and never the Toolkit Name specifically.
Confirmed live 2026-08-24: pristine → `disabled: true`; **any** single field filled
(Name-only OR Url-only) → `disabled: false`.

Submission is still correctly gated — Save with a required field empty fires **no**
`POST .../tools/prompt_lib/{project}`, shows inline `Field is required`, stays on the
create page.

## Why this keeps biting

Only two Save states are safe to assert: **disabled on the pristine form**, **enabled once
anything is touched**. It has now cost two sessions (ELITEA-1921, then ELITEA-1923/1924).

**ELITEA-1924 is the sharp case:** its Objective, step 4 AND a Pass criterion all assert
"Save remains disabled when only the URL is filled". That is false live. Handled per
`.agents/testing.md` § Merge gate → *Analysis-time entry*: the assertion is written as the
**case** states it, `expect.soft()` + `# Known defect: #633`, so the divergence stays a
visible red instead of being silently swapped for the live behaviour (which would be
reverse-masking). Case status `blocked-on-#633`, never `automated`, until a human rules
product-vs-case-text. See #633's 2026-08-24 comment.

Do NOT assert that the pristine disabled state is *caused by* empty required fields — the
cause is `!formik.dirty`.

Related: [[toolkit_form_helper_text_testids]]
