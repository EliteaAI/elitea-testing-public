---
name: A testid-compliant selector can still be an inline POM violation
description: The role-overrides mechanical grep clears a page.locator() that references a compliant UPPER_CASE testid constant — it does NOT clear "locator built in a spec file"
type: feedback
---

## The situation (PR #1098, ELITEA-1999 review, 2026-08-02)

`test_build_with_ai_skill_from_agent.py` had, twice:

```python
skill_card = page.locator(detail_page.SKILL_CARD_SELECTOR.format(skill_id))
expect(skill_card).to_be_visible(...)
```

`SKILL_CARD_SELECTOR` is a real, pre-existing UPPER_CASE class constant on
`AgentDetailPage` (`'[data-testid="skill-card-{}"]'`). Running the
role-overrides.md mandatory mechanical grep for non-testid handles, this hit
is COMPLIANT by that check's own rule ("a hit is COMPLIANT only if... references
an UPPER_CASE class constant whose class-level definition is a `[data-testid=`
string/template").

## Why it's still CHANGES_REQUESTED

That grep answers one question only: *is the selector string itself testid-based?*
It does not answer the separate question `.agents/testing.md` § Locator policy and
`.claude/rules/page-objects.md` both ask: *is the locator constructed inside a
page-object method, or inline in the spec file?* "Locators live ONLY as
page-object class fields... never in spec files" is unconditional — a
testid-compliant string inlined into a test via `page.locator(...)` still
violates it, because no page-object METHOD exists that owns the lookup. Here,
`AgentDetailPage` had a private NAME-keyed `_skill_card(name)` but no public
ID-keyed method wrapping `SKILL_CARD_SELECTOR` — the implementer needed to add
one (e.g. `get_skill_card_by_id(skill_id) -> Locator`) and call that from the
test, not build the locator inline.

## The reusable check

Two independent passes, not one:
1. Mechanical grep (role-overrides.md) — is the STRING testid-based?
2. POM-discipline check (this entry) — for every `page.locator(...)` hit
   (even a compliant one), does a page-object method already return exactly
   that locator? If the test built it fresh from a class constant instead of
   calling a method, that's still inline construction in a spec file — block
   it, and name the missing method in the fix.
