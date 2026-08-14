---
name: Dynamic testid template constants need a wrapper method
description: page.locator(page_obj.SOME_TEMPLATE.format(x)) in a test file is non-compliant even though the constant is a real class field
type: feedback
---

`.claude/rules/page-objects.md`'s sign-off checklist line "Tests don't
contain direct `page.locator()` calls" applies even when the selector comes
from a class-level dynamic-testid TEMPLATE constant (e.g.
`PipelineDetailPage.STATE_VARIABLE_NAME = '[data-testid="pipeline-state-variable-name-{}"]'`).

Touching it directly from a test —
`page.locator(pipeline_page.STATE_VARIABLE_NAME.format("input_attachments"))`
— reads as compliant at a glance (the constant IS a legitimate class field,
per `.agents/testing.md`'s dynamic-testid convention) but is still a raw
locator call in the spec file. The `.format()` interpolation has to happen
INSIDE a page-object method, same as any other locator construction.

**Fix shape**: add a small wrapper method next to the sibling methods that
already use the same template, mirroring their existing style. Example (from
ELITEA-2043, `pipeline_detail_page.py`):

```python
def is_state_variable_present(self, name: str) -> bool:
    """Return whether a STATE panel row for *name* currently exists in the DOM.

    Testid-based (``STATE_VARIABLE_NAME``) — used for its ABSENCE (canon
    ruling #511 extension) to confirm a variable auto-added by a MODULES
    toggle is fully removed from the STATE panel, not merely hidden.
    """
    return self.page.locator(self.STATE_VARIABLE_NAME.format(name)).count() > 0
```

This mirrors the pre-existing `is_state_variable_delete_button_present()`
(same shape, different template constant, `STATE_VARIABLE_DELETE`) —
before reaching for a template constant directly in a test, check whether a
sibling absence/presence-check method already exists for it, or add one in
the same style rather than touching the constant from the spec.
