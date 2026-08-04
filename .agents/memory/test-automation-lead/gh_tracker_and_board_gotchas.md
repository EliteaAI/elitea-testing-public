---
name: gh tracker and board gotchas
description: Silent-failure modes in gh/board mechanics — pagination truncation, quota-cheap read-back, two-part writes, wrong merge flag, auto-close keywords, and the -F/-f and full+json flag traps
type: feedback
---

## Rules

- **`gh project item-list` truncates silently.** A card absent from the result is
  indistinguishable from a card not on the board. Pass `--limit` comfortably above
  the board's real size (board #9 is 560+ and growing → `--limit 1000`); if
  `len(items) == limit`, raise and re-fetch.
- **Read back a single item by node id, not by re-listing.** `item-list` costs
  GraphQL quota proportional to `--limit` and the 5000/hr budget is shared across
  every concurrent session on this machine. Once you hold the `PVTI_…` id:
  `gh api graphql -f query='query { node(id:"PVTI_…"){ ... on ProjectV2Item {
  fieldValueByName(name:"Status"){ ... on ProjectV2ItemFieldSingleSelectValue{name} }
  content{ ... on Issue{number title} } } } }'` — roughly constant cost. Make this
  the default for every post-`item-edit` confirmation, not just an outage fallback.
  Symptom of exhaustion: a `json.decoder.JSONDecodeError` downstream — the real
  `API rate limit exceeded` message is on stderr; print raw `gh` output first.
- **`gh label create` ≠ label applied.** It registers the label repo-wide only;
  attaching is a separate `gh issue edit <N> --add-label <x>`. An interrupted turn
  can post a verdict and skip the attach, leaving the completion signal missing.
  Generalizes to every register-then-set pair (milestones, project field options).
  On resume, re-read `--json labels` rather than trusting memory that it finished.
- **Strip auto-close keywords before merging.** Implementers' PR tooling inserts
  `Closes #N` by habit; a squash-merge then auto-closes an issue that must stay OPEN
  at `Ready`. Grep the PR body for `Closes|Fixes|Resolves #N` (case-insensitive) as
  a standing pre-merge step and rewrite to `Refs #N`. Put it in the gate, not the
  dispatch prompt — instructions get missed, gates don't.
- **`gh pr merge` needs the strategy flag typed explicitly.** Passing `--merge`
  succeeds cleanly with exit 0 and no warning that squash was expected. Say the
  policy line out loud, then type `--squash --delete-branch`. If a wrong-strategy
  merge already landed on `automation/base`: do NOT rewrite history (shared branch,
  force-push forbidden) — declare the deviation in the issue thread.
- **`gh api` `-F` vs `-f`:** only capital `-F/--field` does `@file` substitution;
  lowercase `-f/--raw-field` posts the literal string `@/tmp/x.md` and returns 200.
  (`gh issue comment --body-file` is a different command with no `@` convention.)
  Always read the write back — 200 proves the request, not the content.
- **`body_html` needs an explicit Accept header.** `gh api …/comments/<id> --jq
  '.body_html'` returns `null` by default. Add
  `-H "Accept: application/vnd.github.v3.full+json"`. A default-mediatype fetch
  finding 0 commit-link anchors looks exactly like a real link FAIL —
  sanity-check `wc -c` on the HTML before concluding anything.
- **Bare `EliteaUI#526` actively mislinks.** GitHub's autolinker splits it and links
  the trailing `#526` to THIS repo — a wrong clickable target, not just unlinked
  text. Audit grep: `EliteaUI#` not preceded by `EliteaAI/`; on a hit in free prose,
  pull `body_html` and cite the wrong target's actual title as evidence.
- **`Blocked` on a card whose own log says "→ Ready" is usually a loop-requeue
  artifact, not a delivery defect.** Read the last 2–3 comments: a real blocker ends
  in an open question to a human; the artifact ends in "N sessions without leaving
  this loop's queue. Parking it as Blocked." Flag it, don't re-audit the delivery.
- **Never verify "did this testid land" with a hash ancestor check.** Cherry-pick
  mints a new hash, so `git merge-base --is-ancestor` returns NO even when correct.
  Use `git diff <sha1> <sha2>` (metadata-only diff = same content) or
  `git grep <testid> <ref> -- src/`. **Still live regardless:** before writing a
  closure record, confirm the testid commit was actually **pushed**
  (`git log --oneline -1 <branch>` vs `origin/<branch>`) — chasing a reviewer's
  wrong-method finding is how an unpushed commit got caught.

- **`gh project item-edit` needs `--project-id` in addition to `--id`, `--field-id`,
  `--single-select-option-id`.** Omitting `--project-id` fails; the command prints
  **nothing on success** either way — always confirm the move via the read-back
  technique above (node-id query), never trust the empty return.

## Seen 10×

- #262 audit — `--limit 200` returned the oldest 200 of 564, silently missing #262 (`Ready`).
- Intake run 34 — shared quota exhausted by concurrent sessions' `item-list --limit 700`.
- #268 / PR #678 — verdict posted, `control:audited` label never attached (interrupt).
- …plus 7 earlier occurrence(s) — full per-case detail in the source entries below.

See also: board_pagination_default_silently_drops_recent_items.md ·
board_readback_under_shared_quota_pressure.md ·
label_create_does_not_attach_to_issue.md ·
pr_closes_keyword_auto_closes_ready_issue.md ·
gh_pr_merge_squash_flag_required.md ·
gh_api_body_html_needs_full_json_accept_header.md ·
gh_api_patch_needs_capital_f_for_file_substitution.md ·
bare_reponame_autolink_misdirect.md ·
recurring_ready_vs_blocked_board_discrepancy_228.md ·
cherry_pick_ancestor_check_false_positive.md
