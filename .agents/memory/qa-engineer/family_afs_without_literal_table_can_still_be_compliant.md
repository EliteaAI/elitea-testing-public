---
name: Family AFS without a literal parametrize table can still pass per-row triangulation
description: A single test method + tagged allure.step for the stricter case's own distinct assertion satisfies the reviewer-contract per-ROW rule when the two cases are a strict assertion superset, not divergent values
type: feedback
---

## What

The reviewer contract (`test-automation-workflow` § Triangulate) requires, for a
family spec: "each case id maps to a data-table row whose DISTINCT expected
values are actually asserted... a shared flattened assertion across rows... is
CHANGES_REQUESTED." Read literally this implies `@pytest.mark.parametrize`
with a real data table. It does not have to be that shape.

## When a single shared method is still compliant

Verified on ELITEA-2207/2469 (PR #1599, `tests/2207-2469-hash-search-select-agent-participant`):
2469 is a strict **assertion superset** of 2207 (same flow, same steps, 2469
additionally requires the PARTICIPANTS row to show name+version+icon, which
2207's wording never asks for). The implementer shipped ONE test method
carrying both `@allure.issue(...)` tags, with 2469's extra requirement
implemented as its own explicitly-labeled `allure.step` ("Step 4 (ELITEA-2469)
— ...") containing real assertions (name-in-row-text, version-regex,
icon-visible) that 2207 never needs and never gets.

This is compliant because:
- No case's expected value is ever silently satisfied by an assertion that
  doesn't actually check it (the failure mode the rule exists to catch).
- The stricter case's *distinct* requirement has its own dedicated,
  independently-failing assertion block.
- Precedent already existed in-repo (ELITEA-2179/2466, cited by the AFS).

**The rule to actually apply when reviewing a family AFS that isn't a literal
data table:** ask "if the STRICTER case's requirement silently regressed, would
ANY assertion in this diff fail?" If yes (a dedicated block exists), the family
is triangulated correctly regardless of whether it's shaped as a parametrize
table or a single tagged method. If no — a shared assertion that would stay
green even if the stricter case's extra requirement broke — that's the real
CHANGES_REQUESTED shape, table or no table.

## Where
`test-specs/chat-interface/lextend_hash-search-select-agent-adds-participant-and-responds_ELITEA-2207.md`,
`automation/tests/ui/chat/test_chat_interface.py::TestHashSearch::test_add_agent_via_hash_search_joins_participants_and_responds`.
Origin: reviewer pass, 2026-08-19.
