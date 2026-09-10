# REST is the fallback when the GraphQL rate limit blocks tracker writes

**Learned:** 2026-09-10 (working #2181, ELITEA-2022)

## What happened

Mid-session, every `gh` tracker write started failing:

```
gh: API rate limit already exceeded for user ID 15179789.
{"errors":[{"type":"RATE_LIMIT","code":"graphql_rate_limit",...}]}
```

It hit after ~4 GraphQL calls, and it blocked `gh issue comment` — which is **not**
obviously a GraphQL command, but is one under the hood.

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

## The operational lesson

When the limit hits, **do not stop and do not park the card**. Re-order the session:
push all REST-able work through (investigation, gate runs, every comment, the closure
record), and leave only the board write for the reset. Also **capture the project item
id early** — `PVTI_…` came from the one GraphQL query that succeeded before the limit,
and without it the post-reset move needs an extra lookup.

Grab it up front, in the same query that reads the card:
`projectItems(first:5){nodes{ id project{number} fieldValueByName(name:"Status"){...} }}`
