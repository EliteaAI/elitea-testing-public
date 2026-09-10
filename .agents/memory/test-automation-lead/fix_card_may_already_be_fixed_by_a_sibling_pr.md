---
name: A Fix card may already be fixed — settle it in two commands before dispatching
description: Check the GHA sha against the fix merge, then run a one-file matched control; a sibling's merged PR can already cover the card
type: feedback
aliases: [already fixed, sibling PR covers this card, matched control, negative control, fix card triage]
tags: [area/orchestration, type/triage]
created: 2026-08-28
updated: 2026-09-10
---

## The situation

`[Fix][ELITEA-xxxx]` cards are filed from a GHA failure, and the filing is
automatic — it does not know whether someone has since fixed the cause. When two
specs share a page-object method, one card's PR silently fixes the other's card.
Worked case: #1894 (ELITEA-2003) was already fixed by #1893's PR #1927, which
changed the shared `PipelineDetailPage.confirm_new_version()`.

Dispatching an analyst before checking this burns a full pipeline pass on a
green test.

## Step 0 — the branch check, cheaper than both (2026-09-10, #2121)

Repairs land on `automation/base`; CI's DEV/STAGE workflows run **`main`**, which
receives them only via a human-triggered batch promotion. So **any repair merged
between a CI run and the next promotion regenerates its own card, with a
byte-identical signature**. One command settles it:

```bash
git log origin/main               --oneline -- <failing spec path>
git log origin/automation/base    --oneline -- <same path>   # a repair main lacks => card is stale
git rev-list --left-right --count origin/main...origin/automation/base
```

Worked case: #2121 (ELITEA-2070) cited DEV-stable run #114 on `main@5359201`
(12:50 +0400); the repair `1850761e` merged to `automation/base` at 12:52 +0400 and
`origin/automation/base` was 409 ahead / 0 behind. The card could not have tested the
fix. Correct delivery: verify on the card's own environment, closure record, `Ready` —
no code.

## Step 1 — timing. Could the failure even have seen the fix?

```bash
gh run view <run-id> --json createdAt,headSha,workflowName    # when + what sha
git merge-base --is-ancestor <headSha> origin/main            # is it on the line?
git show <headSha>:<path> | grep -c <token-the-fix-introduced>   # 0 = fix absent
```

`0` plus a fix merged *after* `createdAt` means the card's evidence is stale by
construction. That is two commands and it reframes the whole card.

## Step 2 — matched control. Prove it, do not infer it.

Timing shows the fix *could* cover it. Only a control shows it *does*. Revert
exactly one file and run the same spec on the same tree, minutes apart:

```bash
git show <fix-sha>^:automation/pages/<page>.py > /tmp/prefix.py
cp automation/pages/<page>.py /tmp/postfix.py && cp /tmp/prefix.py automation/pages/<page>.py
cd automation && HEADLESS=true ../.venv/bin/pytest <node-id> -v -p no:cacheprovider --reruns=0
cp /tmp/postfix.py automation/pages/<page>.py     # restore immediately
```

Expect PASS on pristine, FAIL with the card's signature on the reverted tree.
That pair is causation. Same discipline as the `#1082` pristine-HEAD control in
`.agents/testing.md`, pointed the other way: there you exonerate a diff, here you
convict its absence.

Then run the normal 3× gate on the pristine tree and deliver a closure record —
there is no PR to open, and that is a legitimate terminal state. Do not
manufacture a code change to satisfy the card's "MUST deliver a PR" template.

## Gotcha

`-p no:rerunfailures` **fails** on this repo — `pytest.ini`'s `addopts` passes
`--reruns=2 --reruns-delay=5 --only-rerun=...`, which the disabled plugin leaves
unparsed. Use `--reruns=0`.

## Watch for the residual

A sibling's fix often lands on ONE method and leaves the same defect shape in a
neighbour. Read the fixed file's other methods: #1927's own docstring on
`wait_for_fallback_to_base` admitted it kept the pre-fix pattern. That is a new
issue (`Todo`, not started — dispatch rule 7), not scope for this card.

Related: [[sibling_fix_cards_can_have_different_root_causes]] · [[read_the_sibling_card_thread_before_dispatching]] · [[blast_radius_red_classify_with_a_control_run_on_base]]
