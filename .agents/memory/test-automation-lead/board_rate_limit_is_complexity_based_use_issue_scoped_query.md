---
name: Board "API rate limit exceeded" is COMPLEXITY-based — find a card via the issue, never a full board dump
description: gh project item-list --limit 900 fails while rate_limit reports 5000/5000 remaining; a targeted gh api graphql on issue.projectItems works instantly
type: feedback
aliases: [project item-list rate limit, board rate limited, API rate limit exceeded for user ID, gh project graphql limit, find card id]
tags: [area/tracker, type/trap]
created: 2026-09-09
updated: 2026-09-10
---

## The symptom that misleads

```
$ env -u GITHUB_TOKEN gh project item-list 9 --owner EliteaAI --format json --limit 900
GraphQL: API rate limit exceeded for user ID 15179789.

$ env -u GITHUB_TOKEN gh api rate_limit
core:    5000/5000 remaining
graphql: 5000/5000 remaining
```

Both counters full. The message names an hourly-sounding limit and `reset` is up
to an hour out, so the obvious read is "blocked, park or wait". **Wrong.** The
ProjectsV2 GraphQL limit is **node/complexity-based**, evaluated per query — a
900-item board dump exceeds it while a 5-item one sails through seconds later.
Waiting achieves nothing; asking for less achieves everything.

## The replacement — scope by the issue, not the board

Do not page through the board to find one card. Ask the issue for its own item:

```bash
env -u GITHUB_TOKEN gh api graphql -f query='
query { repository(owner:"OWNER", name:"REPO") { issue(number:NNNN) {
  id
  projectItems(first:5) { nodes {
    id
    project { number title id }
    fieldValueByName(name:"Status") {
      ... on ProjectV2ItemFieldSingleSelectValue { name optionId } } } } } } }'
```

Returns the item id, project id and current status in one cheap call. Then the
Status field's options (also cheap, once):

```bash
env -u GITHUB_TOKEN gh api graphql -f query='
query { node(id:"<projectId>") { ... on ProjectV2 {
  field(name:"Status") { ... on ProjectV2SingleSelectField { id options { id name } } } } } }'
```

and move it with `updateProjectV2ItemFieldValue`
(`value:{singleSelectOptionId:"<optionId>"}`).

Board #9 Status option ids, 2026-09-09 (verify rather than trust if a move fails):
`Todo f75ad846` · `Answered 875a713f` · `ReportedBugs 7ab41d6b` ·
`Pre-Approved 3d592706` · `Approved e2a158a3` · `In Progress 47fc9ee4` ·
`Blocked a08c0311` · `Ready 873297dc` · `Promoted b242a9a8` · `Done 98236657`
Field id `PVTSSF_lADOECVEvc4BdCqszhXnG_g` · project id `PVT_kwDOECVEvc4BdCqs`.

## Why it matters in unattended mode

A card left unmoved reads as a failed attempt. Treating this error as "wait an
hour" burns the session for nothing when the fix is one narrower query.

## ⚠️ CORRECTION 2026-09-10 (#2193) — there is ALSO a hard endpoint block, and waiting IS the only move

The rule above ("complexity-based; ask for less and it sails through") is **true but
incomplete**, and taking it as the whole story cost me a wrong first diagnosis today.

On #2193 the 900-item board dump failed as usual — but so did the issue-scoped query, and so
did the cheapest GraphQL call that exists:

```
$ env -u GITHUB_TOKEN gh api graphql -f query='query { viewer { login } }'
{"errors":[{"type":"RATE_LIMIT","code":"graphql_rate_limit",
            "message":"API rate limit already exceeded for user ID 15179789."}]}

$ env -u GITHUB_TOKEN gh api rate_limit --jq .resources.graphql
{"limit":5000,"remaining":5000,"reset":1789070540,"used":0}
```

`viewer { login }` has no complexity to reduce. **So there are two distinct failures wearing
the same error message**, and they need opposite responses:

| Symptom | Which one | Response |
|---|---|---|
| Big query fails, small query succeeds | complexity/points | **ask for less** — issue-scoped query, works instantly |
| *Every* query fails, incl. `viewer{login}` | hard endpoint block | **wait** — `reset` is real, a genuine ~60 min |

**Tell them apart with one probe: `query { viewer { login } }`.** Do it before deciding, and
never quote `remaining: 5000` as evidence you are not limited — that counter is silent about
both failures.

When it is the hard block: REST carries everything except the board move
([[rest_is_the_fallback_when_graphql_rate_limits_tracker_writes]]) — comments, labels, issue
reads all go through `gh api repos/.../issues/...`. Only `updateProjectV2ItemFieldValue` has no
REST equivalent, so the card move is the one thing that must wait out the window. In factory
mode that means waiting **in-turn**, in capped slices
([[waiting_for_a_background_job_in_factory_mode]]) — parking the card `Blocked` for a rate
limit would be wrong: nothing is blocked, the clock just has to run.
