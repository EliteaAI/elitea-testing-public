---
name: CI-red repair cards — read the originating run's log before parking on a local red
description: A local red on a fix card is often a DIFFERENT failure than the CI one; the originating GHA log settles it and can turn a park into a delivery
type: feedback
---

For a `[Fix][<CASE>]` card (a merged/promoted test that went red on CI), two failures are
in play and they are easy to conflate:

1. the **CI** failure the card was filed for, and
2. whatever the test does on **this workstation** after the repair.

They are frequently different. Treating (2) as (1) is how a deliverable card gets parked.

## The move: read the originating run's own log

```bash
env -u GITHUB_TOKEN gh run view <run-id> --repo <repo> --log > /tmp/ci.log
grep -E "<test_name>|<suspected error string>" /tmp/ci.log
```

Worked case — #1816 / ELITEA-1140, 2026-08-27. After the route-drift repair, `[github]`
still failed **locally** at Step 8 on `401 Bad credentials` (expired local `GIT_HUB_TOKEN`,
#1673). The instinct was: unverifiable param ⇒ `Blocked`. The originating run's log said
otherwise — a **sibling test in that very run returned a real branch list** from the repo,
and the whole run contained **zero** `Bad credentials`. So CI's credential was valid, the
CI failure had been *purely* the drift, and the repair cleared the card. Card → `Ready`
instead of `Blocked`, with the local caveat stated rather than hidden.

`--log` also gives per-test PASSED/FAILED lines and full assertion text — often richer than
the issue body, which is written from a truncated stack trace.

## Two companions for this card type

- **The stack trace shows only the FIRST break.** A UI redesign usually drifts several steps;
  the trace stops at one. Instruct the analyst to *walk the whole flow to the end*. #1816's
  second break was a bbox filter (`x > 700`) that, after the panel moved columns, matched
  nothing and **silently returned without filling** — a Step-2-only fix would have shipped a
  fresh red at Step 6. (Same lesson as ELITEA-1866, where the drift spanned 8 steps.)
- **Check whether a just-merged sibling already fixed it.** Reds arrive in waves from one
  redesign. `git log --oneline -5` + `git show <sha> --stat` on the base is cheap, and
  #1816's entire navigation repair was an existing `open_test_surface()` from the sibling
  card's commit.

## The line not to cross

Never let "make the local red go away" drive the repair. #1816's case text specified a
401→skip precondition that would have made `[github]` skip cleanly — implementing it *then*
would have converted the one visible failure into a silent skip and made the merge gate read
green for the wrong reason. It was scoped out and filed separately instead.
