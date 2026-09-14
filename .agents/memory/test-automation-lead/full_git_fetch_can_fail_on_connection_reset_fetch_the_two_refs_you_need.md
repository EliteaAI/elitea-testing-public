---
name: A full `git fetch origin` on the testing repo can die on "Connection reset by peer" — fetch the two refs you need instead
description: Twice in one session the full fetch failed at index-pack (curl 56); `git fetch origin main automation/base` with a bigger postBuffer succeeded in ~10 s and satisfied the fresh-ground-truth rule
type: feedback
aliases: [git fetch fails, curl 56, connection reset by peer, early EOF, fetch-pack invalid index-pack, onedrive fetch, narrow fetch, fresh ground truth blocked]
tags: [area/git, area/triage, type/gotcha]
created: 2026-09-14
updated: 2026-09-14
---

## The failure

On #2276 (2026-09-13) `git fetch origin` in `elitea-testing-public` failed **twice**, ~2 min each,
with:

```
error: RPC failed; curl 56 Recv failure: Connection reset by peer
fetch-pack: unexpected disconnect while reading sideband packet
fatal: early EOF
fatal: fetch-pack: invalid index-pack output
```

The EliteaUI and onetest fetches in the same minute succeeded — so it is the size of this repo's
delta (many nightly-maintenance JSON commits + branches), not the network as such. And the
fresh-ground-truth rule (`.agents/role-overrides.md`) means **no `origin/*` read is valid until a
fetch succeeds** — the message-string grep I had already run was on stale refs and had to be
discarded.

## What worked, first try, in ~10 s

```bash
git -c http.postBuffer=524288000 fetch origin main automation/base
```

Fetching only the refs the check needs (`main` for "what CI ran", `automation/base` for "where the
repair lives") updates `origin/main` / `origin/automation/base` exactly like a full fetch would, so
every downstream `git grep <ref>` / `merge-base --is-ancestor` is still against fresh ground truth.

## Rule

If a full fetch on this repo fails with curl 56 / early EOF, **do not retry the full fetch** — narrow
it to the two refs and move on. Retrying the full fetch cost ~4 min and produced the same error.
Never shallow-clone as a workaround (`.agents/profile.md`).

## Side note — no `timeout` binary on this mac

`timeout 540 bash -c 'until …'` fails with `command not found`. Bounded waits use a counter loop:
`i=0; until <cond> || [ $i -ge 50 ]; do sleep 10; i=$((i+1)); done` inside one Bash call with
`timeout: 600000`.

Related: [[dev_gate_discipline_for_fix_cards]] · [[ancestry_check_is_the_first_move_on_a_fix_card]]
