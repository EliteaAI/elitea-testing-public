---
name: Board "API rate limit exceeded" is COMPLEXITY-based — find a card via the issue, never a full board dump
description: gh project item-list --limit 900 fails while rate_limit reports 5000/5000 remaining; a targeted gh api graphql on issue.projectItems works instantly
type: feedback
aliases: [project item-list rate limit, board rate limited, API rate limit exceeded for user ID, gh project graphql limit, find card id]
tags: [area/tracker, type/trap]
created: 2026-09-09
updated: 2026-09-09
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
