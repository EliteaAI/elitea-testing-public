---
name: List-page getter timeout-swallow masks load failure vs genuine-empty
description: get_card_names()-style list getters catch a wait_for timeout and return [] — can't distinguish "genuinely 0 items" from "page/list failed to render", so a "not in list" absence-assertion trivially passes either way
type: feedback
---

Seen in `automation/pages/mcp_list_page.py::get_card_names()` (pre-existing,
not introduced by any single PR) during ELITEA-1947 PR #621 review:

```python
def get_card_names(self, timeout: int = 5000) -> list[str]:
    try:
        self.mcp_card_name.first.wait_for(state="visible", timeout=timeout)
    except Exception:
        return []
    ...
```

If the wait times out for ANY reason — genuinely zero cards, OR the list
page silently failed to render, OR a network error left the page in a
broken state — the method returns `[]` either way. A test asserting
`assert NAME not in list_page.get_card_names()` (the standard post-delete
absence check, e.g. ELITEA-1947's steps 9/10) passes identically whether
the deletion genuinely succeeded or the page just failed to load. The two
cases are indistinguishable from the assertion's perspective.

Not filed as a defect — this is test-infra, not product, and it's shared
across every spec that calls `get_card_names()` (6+ MCP specs alone, likely
the analogous method on Credentials/Skills/Agents list pages too). Flagging
as a candidate hardening item: a future pass could have the getter surface
*why* it returned empty (raise vs return-empty, or return `None` vs `[]`
to force callers to handle "couldn't determine" separately from "confirmed
empty"), or callers could pair absence assertions with a positive liveness
check (e.g. assert the list container itself rendered) rather than relying
solely on the negative "name not present" signal.

Same shape as the CardList.jsx empty-state/clear-redirect bug class
(`shared_list_search_empty_state_and_clear_redirect_bug.md`) in that it's a
shared list-page component behavior worth auditing broadly rather than
fixing point-by-point per spec.
