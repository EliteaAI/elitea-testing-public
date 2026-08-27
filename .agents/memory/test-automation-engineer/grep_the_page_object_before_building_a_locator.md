---
name: Grep the page object before building a locator in a spec
description: SecretsPage already owned get_row_names() and toast_alert_with_severity() — both were re-implemented inline and blocked at review
type: feedback
aliases: [spec locator, duplicate accessor, get_row_names, toast_alert_with_severity, hard don'ts locators]
tags: [area/implementation, type/anti-pattern]
created: 2026-08-28
updated: 2026-08-28
---

## What happened

ELITEA-2349 built two locators in the spec file — a severity-scoped toast
(`page.locator(SecretsPage.TOAST_ALERT_SEVERITY.format("error"))`) and a
row-name read (`secret_row.locator(SECRET_NAME_CELL_SELECTOR).all_inner_texts()`).
Both accessors **already existed** on `SecretsPage`
(`toast_alert_with_severity()`, `get_row_names()`), so the violation of
`.agents/conventions.md` § Hard don'ts ("never build locators inside methods or
spec files") was also pure duplication. `CHANGES_REQUESTED`.

## The habit

Referencing a page-object CONSTANT from a spec (`secrets_page.SOME_SELECTOR`) is
the tell: a class constant is an ingredient for a page-object method, never for a
spec. When you reach for one, grep the page object for the method that already
uses it:

```bash
grep -n "SOME_SELECTOR" automation/pages/<page>.py
```

`SecretsPage` is ~1000 lines with ~40 accessors — the one you need is usually
there.

## The same grep also prevents a SHADOWED member (fix round 2, same PR)

Round 2 of #1911 caught the mirror defect: this branch *declared*
`toast_alert`, `toast_message` and `TOAST_ALERT_SEVERITY` on `SecretsPage`
when a sibling settings-w05 unit had already merged them into the batch trunk
~120 lines above. Python keeps the **last** definition, so the richer originals
(severity auto-hide durations, the secrets-flow message catalogue) became dead
code — silently.

Nothing on this stack catches it: ruff's `E,F,I,W,UP` has no rule for a
redefined class attribute (`F811` covers imports/functions, not `ast.Assign`
targets), both definitions pass the reviewer's locator grep, and the run stays
green because the shapes are functionally identical.

**Expect it on any long page object touched by more than one unit in a wave** —
units branch from the trunk and merge back one at a time, and git merges two
additions in different hunks without a murmur.

Before adding a class member to a shared page object:

```bash
# by ATTRIBUTE NAME, not by testid — the testid may legitimately appear twice
grep -n "^    <member_name> = " automation/pages/<page>.py
# or the whole-class check (catches methods too)
python3 -c "
import ast,collections,sys
t=ast.parse(open(sys.argv[1]).read())
for n in ast.walk(t):
    if isinstance(n,ast.ClassDef):
        d=collections.defaultdict(list)
        for s in n.body:
            if isinstance(s,ast.Assign):
                d.update({x.id:d[x.id]+[s.lineno] for x in s.targets if isinstance(x,ast.Name)})
            elif isinstance(s,(ast.FunctionDef,ast.AsyncFunctionDef)): d[s.name].append(s.lineno)
        print(n.name,{k:v for k,v in d.items() if len(v)>1})
" automation/pages/<page>.py
```

Pinned for `SecretsPage` by
`automation/tests/unit/test_secrets_access_and_error_spec_invariants.py::TestPageObjectHasNoShadowedMembers`.
The same walk over `automation/pages/*.py` shows the debt is not new:
`ChatPage` (3 shadowed members), `SkillDetailPage` (10), `PipelineDetailPage` (1).
