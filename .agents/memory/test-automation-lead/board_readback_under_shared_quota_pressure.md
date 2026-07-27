---
name: Board read-back under shared GraphQL quota pressure
description: When the shared gh GraphQL rate limit is tight (many concurrent same-machine sessions), verify a single project-item's Status via a targeted node(id) query, not a full item-list --limit N
type: reference
---

## The problem

`env -u GITHUB_TOKEN gh project item-list 9 --owner EliteaAI --limit 700` is
the standard way to find a just-filed issue's project-item id and confirm
its board Status — used routinely for the "read back to confirm the
`item-edit` to Done actually landed" step after every intake-sync run and
after every board mutation more broadly.

**This call costs GraphQL quota proportional to `--limit`, regardless of
how many items you actually need to inspect.** On 2026-07-20 (run 34 of
the intake mission), the shared `gh` GraphQL quota (5000/hour, shared
across every concurrent session on this machine — dozens of parallel
delivery/audit/intake sessions routinely running at once) was fully
exhausted by other sessions' own `item-list` calls. The symptom:

```
GraphQL: API rate limit exceeded for user ID 15179789.
```

surfacing as a `json.decoder.JSONDecodeError` when piping the (empty)
`gh` stdout into `python3 -c "json.load(...)"` — the real error is on
stderr, don't let the JSON decode traceback obscure it; always print/grep
the raw `gh` output first when a downstream parse step fails unexpectedly.

Waiting a short time only recovered the quota from 0 to ~87/5000 — nowhere
near enough headroom for another full 700-item list call, and burning it
on a retry just donates more contention to every other concurrent session
also waiting on the same quota.

## The fix — query the single item directly

Once you already have the project-item id (`PVTI_...`) — e.g. from the
`item-list` call that ran BEFORE the `item-edit`, or from having minted it
yourself in this same turn — skip `item-list` entirely for verification
and query that one node:

```bash
env -u GITHUB_TOKEN gh api graphql -f query='
query {
  node(id: "PVTI_XXXXXXXXXXXXXXXXXXXXXXXXXXXX") {
    ... on ProjectV2Item {
      fieldValueByName(name: "Status") {
        ... on ProjectV2ItemFieldSingleSelectValue {
          name
        }
      }
      content {
        ... on Issue {
          number
          title
        }
      }
    }
  }
}'
```

This costs a tiny, roughly-constant amount of quota (a handful of nodes)
instead of scaling with the full item count (~570+ items and growing).
Confirmed working under quota exhaustion that made `item-list --limit 700`
fail outright.

## Standing recommendation

**Default to the single-node query for ANY board read-back where you
already have the item id** (post-`item-edit` Done-move confirmation,
post-move status checks, etc.) — not just as an emergency fallback when
`item-list` fails. It's cheaper every time, not just under contention, and
the intake-sync loop runs `item-list --limit 700` at least twice per
invocation (once to find the new item's id, once to verify) purely out of
habit copied from the first few runs before the board had many items. The
initial "find the id" lookup after `gh issue create` genuinely needs
`item-list` (or `--search`, but that's explicitly banned for issue-dedup
reasons elsewhere in this project — no reason to think it's safer for
project-item lookups either) since you don't have the item id yet; the
verification step right after does not, and should switch to the
single-node form.
