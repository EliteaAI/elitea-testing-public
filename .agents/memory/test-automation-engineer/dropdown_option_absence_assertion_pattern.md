---
name: Dropdown option absence assertion pattern
description: For asserting a dynamic-testid dropdown option is GONE, use .count()==0 not the presence-waiting helper
type: feedback
---

`is_version_option_visible(name, timeout=...)` (on `PipelineDetailPage` /
`AgentDetailPage`, and the equivalent `*_option_visible` helpers on other
pages with a `[data-testid="…-option-{}"]` dynamic-testid dropdown) is built
to **wait for presence** — it polls up to `timeout` and returns `False` only
after burning the whole wait. That's correct when you expect the option to
show up (possibly with a beat of render lag) but wrong when you're asserting
an option has been **removed** (e.g. after a delete flow) — you'd pay the
full timeout on every green run for no reason.

Pattern used for ELITEA-2003 (`PipelineDetailPage.get_version_option_count`):

```python
def get_version_option_count(self, version_name: str) -> int:
    """Count matching options for `version_name` in the open VERSION dropdown.

    Distinct from `is_version_option_visible` (which WAITS for presence):
    this reads the current count immediately — for asserting ABSENCE.
    """
    return self.page.locator(self.VERSION_OPTION.format(version_name)).count()
```

Reuses the SAME class-level dynamic-testid template constant
(`VERSION_OPTION = '[data-testid="version-option-{}"]'`) the presence-waiting
method already uses — this is the sanctioned dynamic-testid pattern
(`.agents/testing.md` § Locator policy), not a new raw handle; the mechanical
reviewer grep treats it as compliant (references an UPPER_CASE class constant
whose class-level definition is a `[data-testid=` template).

If a page already has a `*_option_visible(name)` helper and a case needs an
absence assertion, check for a `*_option_count(name)` sibling before adding a
new one — likely reusable across pages sharing the same dynamic-testid family
(VERSION_OPTION exists near-identically on `PipelineDetailPage`,
`AgentDetailPage`, `SkillDetailPage`).
