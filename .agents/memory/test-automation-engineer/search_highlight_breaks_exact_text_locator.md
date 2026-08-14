---
name: Active search highlighting breaks Playwright's exact text="..." locator
description: While a search term is highlighted in an entity-card name, exact text="..." locators return 0 even though el.textContent is correct — read via the entity-card-name testid + .text_content() instead.
type: feedback
---

## Rule

Any entity-card list page (Agents/Credentials/MCP/Skills/Pipelines/Toolkits —
all share `Card.jsx`) that highlights the matched substring during an active
search splits the card name into nested `<span>` fragments, e.g.:

```html
<span data-testid="entity-card-name">
  <span>autotest_</span><span class="css-...">YAML</span><span>_search_a62cfb</span>
</span>
```

`element.textContent` on the outer span concatenates correctly
(`"autotest_YAML_search_a62cfb"`), but Playwright's exact `text="..."`
locator engine (`:text-is()` under the hood) does **NOT** match the parent
on that concatenated text when the text is split across child elements —
confirmed live: `page.locator('text="<exact-name>"').count()` → `0` against
the identical page state where `el.textContent` was correct. This silently
breaks any `pipeline_exists_in_list()`/`agent_exists_in_list()`-style helper
(raw `text="..."` locator, tech debt per `.agents/testing.md`) for POSITIVE
assertions made while the grid is actively filtered/highlighted. Negative
(absence) assertions and unfiltered/baseline/restored-list checks are NOT
affected — no highlighting is present in those states.

## Fix

Use the shared `entity-card-name` testid directly and read each card's own
`.text_content()` — this is immune to the split, since it's not asking
Playwright's text engine to match the parent across children:

```python
entity_card_name = LocatorDescriptor(testid="entity-card-name", ...)

def get_card_names(self, timeout=5000) -> list[str]:
    try:
        self.entity_card_name.first.wait_for(state="visible", timeout=timeout)
    except Exception:
        return []
    return [self.entity_card_name.nth(i).text_content() or "" for i in range(self.entity_card_name.count())]
```

Then assert via `name in get_card_names()` instead of the legacy
`pipeline_exists_in_list(name)` whenever the grid may be in a filtered
(highlighted) state. `.filter(has_text=name)` also works (substring match
handles the split fine) if you only need a count, not the full name list.

## Seen 1×

- ELITEA-2023 (`test_pipeline_management.py::test_search_placeholder_and_dashboard_grid_filters_and_clears`,
  2026-08-07) — added `PipelinesListPage.entity_card_name` + `get_card_names()`.
  Related but distinct root cause from `agent_card_names_locator_fix.md`
  (that one was a broken CSS+text-engine compound locator with 0 callers,
  unconditionally returning `[]`; this one is a correct-looking exact-text
  locator that only breaks specifically during active-search highlighting).
  Both fixes converge on the same `entity-card-name` testid + `.text_content()`
  pattern — check for it before reinventing a card-name reader on any
  entity-card list page.
