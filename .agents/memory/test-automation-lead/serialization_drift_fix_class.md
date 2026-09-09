---
name: A serialization change is its own [FIX]-card class — the observable is correct, only its rendering moved
description: Assert the PARSED structure, never a normalized string; and check the steps BEHIND the failure, because a red stops at the first break and hides the rest
type: feedback
aliases: [serialization drift, python repr vs json, pretty printed json assertion, assertion pinned to a format, first break hides the rest]
tags: [area/triage, type/lesson]
created: 2026-09-09
updated: 2026-09-09
---

## The shape

ELITEA-1866 (#2066): a merged test asserted
`"{'total': 0, 'rows': []}" in result_text` — a **Python-repr** serialization.
The product began emitting valid JSON, so EliteaUI's `prettifyToolkitMessage`
(`JSON.parse` → `JSON.stringify(parsed, null, 2)`) took its pretty-print path
and the same value rendered as `{ "total": 0, "rows": [] }`.

**Nothing about the product's behaviour changed and nothing was wrong with it.**
The bucket really was empty, which is what the case came to verify. The test
had pinned one *encoding* of a correct answer.

Tell it apart from a real regression in one look: the failure message shows the
**same semantic value in a different shape**. A regression shows a different
value.

## Repair: parse and compare structure

```python
assert "list_files" in result_text          # keep the identity check
payload = parse(result_text)                 # split on the ✅/❌ marker, (\{.*\})\s*$, json.loads → ast.literal_eval
assert payload == {"total": 0, "rows": []}
```

The `literal_eval` fallback keeps the *pre-drift* form parsing too, so the test
survives a revert.

**Reject normalization** (stripping whitespace, swapping quote styles): it
survives *this* drift and not the next one, which is how the same card comes
back. Reject reading the raw `<pre>` element: no testid, and it is a shared
markdown renderer.

**Say honestly what the new assertion is.** Parsed-structure equality is
stronger on position, extra/renamed keys, and missing payload — but Python's
`==` is not type-strict (`{"total": False}` and `{"total": 0.0}` both compare
equal), so "strictly stronger" is an overclaim. The reviewer caught it committed
verbatim in four places. `.agents/role-overrides.md` § "precedent is not
authority" is explicit that a borrowed authority-word is how drift passes gates.

## The bigger lesson: a red stops at the FIRST break

The card named one cause. The analyst's live walk of the *remaining* steps found
a second sitting right behind it — Step 32's `navigate_to_artifacts()` on a
`networkidle` wait (#1847) that already failed on a pristine page. Fixing only
the reported assertion would have delivered the next red, and cost another full
session.

**Always dispatch the analyst to walk the steps AFTER the failure point**, not
just the failing one. Steps behind a failed step never executed, so CI has told
you nothing about them.

Related: [[a_fix_card_can_have_no_work_in_it]] · [[fix_card_may_already_be_fixed_by_a_sibling_pr]] · [[assertions_behind_a_failing_step_never_ran]] · [[a_product_change_is_not_a_product_bug]]
