---
name: Gate the EXACT CI commit (detached) when the call path differs main↔base — and return to base before any memory write
description: A null-delta FIX card's gate certifies "the artifact that produced the red is green on the env it came from"; with ~20 page-object repairs on base, gating your automation/base checkout certifies a different artifact. `git checkout --detach <ci-sha>` is clean when the tracked tree is clean — but it rewrites the tracked .agents/memory (883 files), so memory writes wait until you are back on base.
type: feedback
aliases: [detached checkout gate, gate the CI commit, which artifact to gate, memory rewritten by checkout, outage card gate, class D gate artifact]
tags: [area/gate, area/triage, type/procedure]
created: 2026-09-15
updated: 2026-09-15
---

## The choice (#2296, ELITEA-2441, 2026-09-15)

The spec was byte-identical on `main`, `automation/base` and CI commit `720b21a`, but the **call
path** (`skill_form_page.py`, `base_page.py`, `conftest`, `api/client.py`) carried ~20 base-only
commits. A green gate on my `automation/base` checkout would have certified *base's* artifact,
not the one CI ran. For a Class-D (outage) verdict the claim in the closure record is precisely
"the artifact that produced the red is green on DEV" — so the gate must run on that artifact.

```bash
git status --short | grep -v '^??'          # must be empty — tracked tree clean
git checkout --detach 720b21a               # the card body's "Commit:" line
# gate (…-p devenv, --reruns=0, 3 runs…) with HEAD echoed into the summary line
git checkout automation/base                # BEFORE any memory/daily-log write
```

`--reruns=0` on the CLI overrides `pytest.ini`'s `--reruns=2`, so every attempt is a visible
invocation result — no `reruns.json` reading needed, and a goto-hazard burst shows as a red run
to re-gate rather than a hidden rerun.

## The hazard the checkout carries

`.agents/memory/**` is **tracked** (1640 files) and differs main↔base — the detached checkout
rewrote 883 files / 40 985 deletions under `.agents/memory`. Nothing was lost because the tree was
clean and I checked base out again before writing — but a memory Write or daily-log append while
detached lands in a detached working tree and is silently dropped by the return checkout. Order is
load-bearing: **gate → `git checkout automation/base` → memory**. If memory edits already exist
uncommitted, stash them first ([[promotion_gap_card_with_no_main_pr_is_closed_by_your_own_cherry_pick]]).

## The cheapest one-off proof for an outage card: the nightly BEFORE and AFTER

`test-results-dev-stable-<user>-<N>` artifacts of the adjacent runs carry `junit.xml`; a
`<testcase>` with no `failure`/`error` child on both sides of the red run (here 06:55Z and
09:45Z around a 07:54Z outage) converts "chronically red" into "one-off" before any gate, and
covers the block's sibling specs for free. Pair it with the shard timeline from
[[env_outage_page_is_a_fix_card_root_cause]].

Related: [[a_null_delta_card_still_owes_a_full_gate]] · [[dev_gate_discipline_for_fix_cards]] ·
[[the_devenv_plugin_is_the_factory_safe_dev_gate]]
