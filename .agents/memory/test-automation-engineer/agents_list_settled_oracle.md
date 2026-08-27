---
name: Agents list settled oracle (load-vs-content)
description: Assert a list page LOADED via entity-card-name OR empty-state-title, never via card count
type: feedback
---

**A list-page "did it load?" check must never be a content check.** Asserting
"at least one card renders" is an *environment* assumption: on deployed envs
each shard user owns only what the specs seed and clean up, so a project
legitimately holds zero entities. That is what made ELITEA-1901 red on
dev.elitea.ai (GHA run 32931571484) while staying green on localhost, whose
shared identity has ~20 leftover agents.

**The compliant oracle** (`AgentsListPage.LIST_SETTLED_SELECTOR` /
`wait_for_list_settled()`, added 2026-08-27, PR #1852):

```python
LIST_SETTLED_SELECTOR = (
    '[data-testid="entity-card-name"], [data-testid="empty-state-title"]'
)
```

It is *stronger* than a card-count check, not weaker: EliteaUI
`src/components/CardList.jsx:40-42` gates BOTH renders behind
`!isLoading && (isError || isEmptyList)` / `... && !isError`, so the
disjunction cannot be satisfied while the list is still loading or has
errored. A `get_agent_card_names()` truthiness check could silently tolerate
exactly that, because the method swallows its `wait_for` timeout and returns
`[]`.

**Scope it when you write the comment: card view, non-folder view.** Two
settled, non-error renders match NEITHER branch — an empty *folder* view
(`PrivateAgentsList.jsx:224-227` passes a bare testid-less
`<Typography>No items in this folder yet</Typography>` as `customEmptyState`,
so `EmptyListBox` never renders) and *table* view (`entity-card-name` lives
only in `Card.jsx:270`; `DataTable` has no equivalent). Also note the
selector is page-level and unscoped: a future shared empty state on the same
route would satisfy the oracle spuriously.

**`empty-state-title` is generic and shared** (`EmptyStatePage.jsx:49`) —
already bound by `ToolkitsListPage` and `McpListPage`, so the same pattern
transfers to Skills / Pipelines / Credentials / MCP list pages verbatim.

**Verifying the empty branch honestly, without substitution:** you usually
cannot reach a genuinely empty project on localhost. Drive the product's own
**zero-match search** instead — `CardList.jsx:41`'s `isEmptyList` does not
discriminate a zero-match search from an empty project, so both take the
identical `showCustomEmptyState` branch. Do it as a throwaway MCP
observation, never baked into the test, and say in the Run Report which
branch the green run actually exercised.
