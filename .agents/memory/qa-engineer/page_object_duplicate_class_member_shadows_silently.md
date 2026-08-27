---
name: A page object can gain a DUPLICATE class member and nothing complains
description: New LocatorDescriptor/constant appended to a long page object silently shadows an identical earlier one — grep alone misses it; run an AST duplicate-member check on every page-object diff.
type: feedback
aliases: [duplicate class attribute, shadowed LocatorDescriptor, page object dead code, redefined descriptor]
tags: [area/review, type/technique]
created: 2026-08-28
updated: 2026-08-28
---

## The trap

`automation/pages/secrets_page.py` is >1000 lines. On PR #1911 (settings-w05,
ELITEA-2349) the implementer appended `toast_alert`, `toast_message` and
`TOAST_ALERT_SEVERITY` to `SecretsPage` — all three **already existed** ~120
lines above, added by a sibling unit that had merged into the batch trunk
before the branch was cut. Python takes the LAST definition: the earlier,
richer ones (severity durations, the secrets-flow message catalogue) became
dead code, silently.

Nothing catches this. Not ruff (no rule for a redefined class attribute in the
default `E,F,I,W,UP` set — `F811` covers imports/functions, not `Assign`
targets), not the reviewer's locator grep (both definitions are compliant),
not the test run (the shapes are functionally identical). The next maintainer
edits the well-documented block and their change does nothing.

## The check — one command, run it on every page-object diff

```bash
git show <branch>:automation/pages/<file>.py > /tmp/po.py && python3 - <<'PY'
import ast, collections
tree = ast.parse(open('/tmp/po.py').read())
for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef):
        lines = collections.defaultdict(list)
        for st in node.body:
            if isinstance(st, ast.Assign):
                for t in st.targets:
                    if isinstance(t, ast.Name): lines[t.id].append(st.lineno)
            elif isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
                lines[st.name].append(st.lineno)
        print(node.name, {k: v for k, v in lines.items() if len(v) > 1})
PY
```

Cheap, static, and it is the only thing that sees the defect.

## Why it recurs on this pipeline

Batch units are cut from the trunk and merged back one at a time, so a page
object legitimately grows from several branches. An implementer who greps
their own diff — or greps for the *testid* rather than the *attribute name* —
sees no conflict, and git merges two additions in different hunks without a
murmur. Expect this class on any long shared page object touched by more than
one unit in a wave.

Related: [[grep_the_page_object_before_building_a_locator]]
