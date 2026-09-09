---
name: A merged PR's "Out of scope" section is a work order for a future card
description: Before dispatching an analyst on a FIX card, grep merged PR bodies for the failing symbol — the previous delivery often already diagnosed it by name
type: feedback
aliases: [out of scope section, prior PR named this defect, FIX card already diagnosed, routing note in PR body]
tags: [area/triage, type/shortcut]
created: 2026-09-09
updated: 2026-09-09
---

## The move

This team's implementers write an **"Out of scope — for routing, not fixed here"** section
into PR bodies. Those items are real diagnoses that nobody carded. When a `[FIX]` card
lands, the cheapest first search is the PR bodies, not the code.

Worked case (#2077 / ELITEA-2063): PR #2058 — the *agent-side* repair of the same
mechanism — contained

> `PipelineDetailPage.close_versions_menu()` … has the identical defect … **this is the
> mechanism behind the pipelines case (ELITEA-2063)**

naming the file, the method and the case id. The root cause was found before any subagent
was dispatched; the analyst's job shrank to *verify live and specify*, not *discover*.

```bash
env -u GITHUB_TOKEN gh pr list --repo <repo> --state merged --limit 60 --json number,title,body \
  | python3 -c "import json,sys; [print(p['number'],p['title']) for p in json.load(sys.stdin) if '<symbol>' in (p['body'] or '')]"
```

## The mirror image — check the accused PR's file list first

The same card blamed the commit under test ("this PR is a fix for the VERSION dropdown,
so it likely regressed it"). One command refuted it:

```bash
env -u GITHUB_TOKEN gh pr view <n> --repo <repo> --json files --jq '[.files[].path]'
```

That PR never touched the failing page object. **An intake card's blame attribution is a
generated guess, not evidence** — cost of checking: one command; cost of believing it: an
analyst sent to bisect a PR that cannot be the cause.

Related: [[nightly_fix_card_traceback_is_not_the_failure]]
