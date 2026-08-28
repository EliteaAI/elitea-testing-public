---
name: Harvest the GHA allure artifacts before dispatching anyone
description: The failure screenshot usually names the root cause in one look, for ~3 tool calls, before any subagent spends context
type: feedback
aliases: [allure artifacts, GHA failure evidence, failure screenshot, download artifacts, fix card first move]
tags: [area/triage, type/lesson]
created: 2026-08-28
updated: 2026-08-28
---

## The move

On any `[Fix]` card citing a GHA run, get the picture **before** dispatching:

```bash
env -u GITHUB_TOKEN gh api repos/<owner>/<repo>/actions/runs/<id>/artifacts \
  --paginate --jq '.artifacts[] | select(.name|startswith("allure-results")) | "\(.id) \(.name)"'
# then per id: gh api repos/<owner>/<repo>/actions/artifacts/<id>/zip > a.zip; unzip -q
grep -l "<test_name>" *.json          # find the -result.json
```

Then read the `-result.json` for the message + per-step statuses, and **Read the
attached screenshot** — it renders inline.

## Why it pays

Two sessions running, it has been decisive both times:

- #1890: the screenshot showed the popper open with a **"Loading…"** placeholder
  → a load race, root cause in one look.
- #1891: the screenshot showed the correct dropdown open **and** a stray
  "Select LLM Model" tooltip → the returned popper was the tooltip. Nothing in
  the log said so; the assertion message alone supported three wrong theories.

Cost ~3 tool calls. The alternative is an analyst hunting live with no prior.

## Two details worth keeping

- **Shards:** the test may sit in any one of a dozen `allure-results-*`
  artifacts. Loop and `grep -l`; do not guess by name.
- **Two shards failing byte-identically is a determinism finding** — say so in
  the dispatch, it changes how the analyst treats a non-reproduction.
- `pytest-rerunfailures` makes junit record PASS for a rerun-recovered failure —
  allure is the only place the original signature survives.

Related: [[sibling_fix_cards_can_have_different_root_causes]] · [[deployed_only_failure_claims_are_hypotheses]]
