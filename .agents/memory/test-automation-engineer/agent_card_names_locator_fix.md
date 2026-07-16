---
name: AgentsListPage.get_agent_card_names() was silently broken until ELITEA-1869
description: The pre-existing get_agent_card_names() locator always matched 0 elements (CSS-list + chained-text-engine selector parsed as one chain by Playwright); fixed to use the entity-card-name testid. Check this before trusting any historical reference to the old shape.
type: feedback
---

## What was wrong

`AgentsListPage.get_agent_card_names()` (and the `AgentPage` facade method that
delegates to it) used this locator:

```python
cards = self.page.locator('[class*="CardContent"] >> text, [class*="cardContent"] >> text')
```

This mixes a CSS selector list (`sel1, sel2`) with a chained Playwright
text-engine selector (`>> text`) in a **single locator string**. Playwright
parses the whole string as one locator chain — the comma is consumed inside
the chain rather than acting as a top-level OR — so `cards.count()` was
always `0`, and the `try/except` around `cards.first.wait_for(...)` silently
swallowed the timeout and returned `[]`.

**Repo-wide grep before ELITEA-1869 confirmed zero callers of this method
in any merged test** — it was dead/untested code, not a shared-caller
regression risk. Discovered when `test_agent_back_navigation.py`
(ELITEA-1869) asserted `agents_before` non-empty against a dashboard that
*visually* had 6 agents (confirmed via a failure screenshot) and got `[]`.
Root-caused with a standalone Playwright script run directly against
`localhost:5173` (not via pytest) — `[class*="CardContent"]` alone matched 6
elements; the compound locator matched 0.

## The fix (already applied, ELITEA-1869)

Each agent card wraps its name in `data-testid="entity-card-name"`. Fixed:

```python
ENTITY_CARD_NAME = '[data-testid="entity-card-name"]'
...
cards = self.page.locator(self.ENTITY_CARD_NAME)
```

Verified: returns exactly the visible agent names in DOM order, no trailing
"TB" (Test Bot avatar-initials) noise the old broken locator would have
picked up had it worked at all.

## Action for future agents

- If you see the OLD `'[class*="CardContent"] >> text, ...'` shape
  referenced anywhere (old AFS text, a stale comment, another page object
  with the same anti-pattern) — don't trust it. Verify against the live DOM
  with a standalone Playwright script before reusing the pattern.
- `entity-card-name` is the correct, testid-compliant handle for reading
  card names on the Agents dashboard (and likely other entity-card list
  pages — Skills/Toolkits/Credentials/MCPs share the same card component
  per `credential_pin_unpin_quirks.md`'s PinButton note; check for the same
  testid there before reinventing a card-name reader for those pages).
- General lesson: a page-object method with 0 merged callers is *unverified
  code*, not battle-tested code — don't assume a helper "must work" just
  because it looks plausible and has a docstring. If your AFS's expected
  behavior mismatches a helper's actual return value, suspect the helper
  with a standalone repro before assuming your test/case understanding is
  wrong.
