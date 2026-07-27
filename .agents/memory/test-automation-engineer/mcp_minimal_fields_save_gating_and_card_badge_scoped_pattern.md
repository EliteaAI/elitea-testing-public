---
name: MCP minimal-fields Save-gating and scoped card-badge locator pattern
description: is_save_button_disabled() dirty-based-Save gotcha (assert only pristine-disabled and both-filled-enabled, never an intermediate single-field state) and the CARD_TAG_CHIP_SELECTOR scoped-selector recipe for reading one specific list card's badge text — both new McpFormPage/McpListPage methods, first used ELITEA-1921, reusable for any entity-card-tag-chip badge read since CardTagSectionItem.jsx is shared across every entity-list type
type: feedback
---

## Save button is dirty-based, not completeness-based

`McpFormPage.is_save_button_disabled()` (new, ELITEA-1921) wraps
`save_button.is_disabled()`. Confirmed live: Save flips from
disabled→enabled the instant ANY field is touched, not once all required
fields hold values. Only assert two states — pristine-form-disabled and
both-required-fields-filled-enabled. An intermediate "still disabled after
only Name filled" assertion is a documented flake trap (CLARIFICATION
`EliteaAI/elitea-testing-public#633`); client-side Yup validation still
correctly blocks submission of an incomplete form regardless, so this isn't
a functional gap, just an assertion-writing trap for the next case that
touches this form's Save button.

## Scoped card-badge locator recipe (`entity-card-tag-chip`)

`entity-card-tag-chip` is a shared, generic testid from `CardTagSectionItem.jsx`
— rendered on every entity-list card type (Toolkits/MCPs/Applications/Skills/
Pipelines/…), one chip per tag, collection-style. A plain
`LocatorDescriptor(testid="entity-card-tag-chip")` would resolve to EVERY
card's chip on the page, not just the one for a specific entity name — not
useful for "does card X show badge Y" assertions.

The compliant pattern (added to `McpListPage`, reusable verbatim on any
other `*ListPage`): an UPPER_CASE scoped-selector class constant (NOT a
`LocatorDescriptor` — page-objects.md's "Scoped selectors" pattern), used
inside a name-filtered card locator:

```python
CARD_TAG_CHIP_SELECTOR = '[data-testid="entity-card-tag-chip"]'

def get_card_type_badge_text(self, name: str, timeout: int = UI_ELEMENT_TIMEOUT) -> str:
    card = self.mcp_card.filter(has_text=name)
    card.first.wait_for(state="visible", timeout=timeout)
    chip = card.first.locator(self.CARD_TAG_CHIP_SELECTOR).first
    chip.wait_for(state="visible", timeout=timeout)
    return chip.text_content() or ""
```

No network-layer assertion is possible for badge text on MCPs specifically —
the list API response carries no `tags` field; the badge is synthesized
client-side from the toolkit's `type` (`ToolkitsHelpers.enhanceToolkitData()`).
DOM read is the only signal.

(from ELITEA-1921, PR #634 — implementer pass, zero defects found, AFS
predictions matched the live surface exactly, GREEN 3/3 first attempt)
