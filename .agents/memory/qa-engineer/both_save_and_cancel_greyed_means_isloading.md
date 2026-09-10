---
name: Both Save AND Cancel greyed means a request is in flight (Elitea forms)
description: Read the DISABLED pair, not just Save — it separates "premature assertion" from "button was a no-op"
type: feedback
aliases: [save greyed, disabled save button, cancel disabled, isLoading, toolkit save race, formik dirty]
tags: [area/toolkits, area/credentials, type/triage-heuristic]
created: 2026-09-10
updated: 2026-09-10
---

## The heuristic

On Elitea's create forms the two tab-bar buttons have *different* disable conditions,
so the PAIR is a state readout — a single greyed Save tells you almost nothing.

`src/pages/Toolkits/CreateToolkitToolTabBar.jsx`:

```js
shouldDisableSave = isLoading || !formik.dirty      // validity is NOT part of it
<DiscardButton title="Cancel" disabled={isLoading}/>  // Cancel: isLoading ONLY
```

| what a failure screenshot shows | what it means |
|---|---|
| Save DISABLED, Cancel **enabled** | `!formik.dirty` — the form was never dirtied, or a `resetForm` wiped it |
| Save **and** Cancel both DISABLED | `isLoading` — **a request is in flight**; the save is happening, the test asserted too early |
| both enabled, no request fired | the click landed but validation blocked it — no POST, no error toast, no navigation |

Verified live on the toolkit create form, 2026-09-10 (#2123 / ELITEA-1141), all four rows.

## Why it mattered

#2123 was filed as *"a product regression in the toolkit creation flow"*. The two CI
failure screenshots showed a filled form with a greyed Save — which reads as
"the button was disabled, the click was a no-op" (the [[#1897]] `test_create_credential`
shape). **Cancel was greyed too**, which rules that out: the create POST was pending and
returned 201 moments later. The test had a fixed `wait_for_timeout(3000)` budget and an
instantaneous URL assert. False RED on a successful save.

Look at Cancel before you conclude anything about Save.

Related: [[networkidle_is_not_a_save_signal_on_elitea]] · [[elitea_save_enabled_is_not_a_validity_oracle]]
