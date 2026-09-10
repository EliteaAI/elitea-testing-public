# REST is the fallback when the GraphQL rate limit blocks tracker writes

**Learned:** 2026-09-10 (working #2181, ELITEA-2022) · **re-hit same day** (#2182, ELITEA-2453) — measured window **~55 min**, 15:29→16:22Z

## What happened

Mid-session, every `gh` tracker write started failing:

```
gh: API rate limit already exceeded for user ID 15179789.
{"errors":[{"type":"RATE_LIMIT","code":"graphql_rate_limit",...}]}
```

It hit after ~4 GraphQL calls, and it blocked `gh issue comment` **and `gh issue view`** —
neither is obviously a GraphQL command, but both are under the hood.

⚠️ **`gh project item-list` reports it as `unknown owner type`** — a completely misleading
message that reads like a bad `--owner` argument. Before debugging the owner, run
`gh api graphql -f query='query{viewer{login}}'`; if that returns the RATE_LIMIT error,
the owner was never the problem.

## The two things worth knowing

1. **`gh api rate_limit` LIED about it.** It reported `graphql: {limit:5000,
   remaining:5000, used:0}` while GraphQL queries were being refused. Do not use it to
   decide whether to wait — try the call. (The `reset` timestamp it gave was ~57 min out,
   and that one did appear to be real.)

2. **REST still worked, with 4906/5000 core remaining.** Issue comments have a REST
   endpoint, so the work log is NOT blocked:

   ```bash
   python3 -c "import json;print(json.dumps({'body':open('/tmp/c.md').read()}))" > /tmp/c.json
   env -u GITHUB_TOKEN gh api repos/OWNER/REPO/issues/N/comments \
     --method POST --input /tmp/c.json --jq '.html_url'
   ```

   The `--input` + JSON-via-python route also sidesteps shell quoting on long markdown
   bodies with backticks and `$`.

## What is genuinely blocked

**Projects V2 has no REST API.** `gh project item-list / field-list / item-edit` are
GraphQL-only, so the **board move** is the one deliverable that must wait for the reset.
Everything else — comments, issue reads (`gh api repos/.../issues/N`), issue search
(`search/issues`), PR reads, Actions API — can proceed over REST.

## Unrelated trap in the same command — `--limit`

`gh project item-list 9 --owner EliteaAI` silently truncates. Board #9 holds **1018**
items, so `--limit 900` returned a full-looking list that simply did not contain my own
card. **Always `--limit 3000`** and assert the card you expect is in the result.

## The operational lesson

When the limit hits, **do not stop and do not park the card**. Re-order the session:
push all REST-able work through (investigation, gate runs, every comment, the closure
record), and leave only the board write for the reset. Also **capture the project item
id early** — `PVTI_…` came from the one GraphQL query that succeeded before the limit,
and without it the post-reset move needs an extra lookup.

Grab it up front, in the same query that reads the card:
`projectItems(first:5){nodes{ id project{number} fieldValueByName(name:"Status"){...} }}`

---

## Third hit the SAME day — 2026-09-10, working #2183 (ELITEA-1899)

Started ~16:22Z, still refusing at **16:45Z**. Tripped by exactly what the note above warns
against: a `gh project item-list --limit 3000` followed by a
`gh api graphql --paginate --slurp` board walk. Two calls. The prior successful
`--limit 900` call is what lures you into escalating.

**Confirmations of the existing entries** — `gh api rate_limit` again reported
`graphql 0/5000 used, remaining 5000` while every GraphQL call was refused, and
`gh project item-list` again mis-reported it as **`unknown owner type`**.

**Simpler REST comment recipe than the python-JSON one above** — `gh api` accepts a file
directly, so no temp JSON and no shell-quoting dance:

```bash
env -u GITHUB_TOKEN gh api -X POST repos/OWNER/REPO/issues/N/comments \
  -F body=@/tmp/comment.md --jq '.html_url'
```

**Labels are REST too** (`gh issue edit --add-label` is GraphQL and blocked):

```bash
env -u GITHUB_TOKEN gh api -X POST repos/OWNER/REPO/issues/N/labels \
  -f "labels[]=duplicate" --jq '[.[].name]|join(",")'
```

**PR mergeability is REST too** (`gh pr view` is GraphQL):
`gh api repos/OWNER/REPO/pulls/N --jq '{mergeable,mergeable_state}'`.

⚠️ **`gh issue view` and `gh issue comment` are GraphQL and blocked; `gh api repos/.../issues/N`
is REST and is not.** With those three substitutions the ONLY blocked deliverable is the
board move — same conclusion as the first two hits, now three-for-three.

**Do not burn the wait on retries.** The limit is time-based here (unlike the
complexity-based ProjectsV2 one in
`board_rate_limit_is_complexity_based_use_issue_scoped_query.md`) — narrowing the query does
NOT help once it is tripped, because even a 1-node `repository{issue{projectItems}}` query is
refused. Spend the window on gate runs and comments; retry the board move on a wide interval.
