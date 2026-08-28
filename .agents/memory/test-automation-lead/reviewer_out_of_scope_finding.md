---
name: A reviewer's out-of-scope "sibling instance" finding must be verified against the ref before it becomes a card
description: The external findings a reviewer volunteers are the least-verified part of a review — they sit outside the diff they were asked to check, so confirm them yourself or you file a card for work already done
type: feedback
aliases: [reviewer external finding, sibling instance, file another card, non-blocking finding, out of scope finding, false card]
tags: [area/review, area/orchestration, type/trap]
created: 2026-08-28
updated: 2026-08-28
---

## The trap

A good reviewer returns more than a verdict: "…and by the way, `<other_spec>.py:95`
has the identical unfixed defect — it needs its own `[Fix]` card." That reads as a
gift, and the instinct is to file it.

**Do not file it on the reviewer's word.** Everything else in the review was
verified against the diff they were handed. The external finding was not — it is
about a file nobody asked them to read, produced by a quick grep at the end of a
long session, and it is the one claim in the report with no gate behind it.

## What it actually costs

Filing lands a card in the entry column, where the factory picks it up as real
work. A false card burns a whole session before anyone notices the fix is already
there — and it is discovered by an agent who trusts the card, not by one looking
for a mistake.

## The failure mode, concretely (ELITEA-2065 / #1892, 2026-08-28)

The review reported `test_pipeline_mcp_node_fresh_attach.py:95` as a still-exposed
instance of a lazy-load race, quoting two real lines:

```
:86  popper = pipeline_page.open_mcp_popper(...)
:95  assert pipeline_page.get_mcp_popper_menu_item_count(popper) > 0
```

Both lines exist, so the finding looks checked. But **line 94 is the wait** — added
by the sibling card's own PR days earlier. The grep matched the two endpoints and
the conclusion "no wait between" was inferred from their absence in the grep output,
never from reading the span.

**A grep proves what it matched. It cannot prove what lies between two matches.**
That is the whole class: a negative claim derived from a positive-match tool.

## The check — cheaper than the report that raised it

Resolve the claim against the ref, not the reviewer's prose. For a
"still-exposed instance" claim, enumerate every call site of the guarded thing and
show the guard next to each:

```bash
for f in <each candidate spec>; do
  echo "=== $f ==="
  git show origin/main:automation/tests/.../$f.py | grep -nE "<guard>|<guarded call>"
done
```

Adjacent line numbers (`:94 wait` / `:95 count`) settle it in one read. Two shell
calls, and it turned "file a card" into "the class is fully closed" — which is a
better closure record than the card would have been.

Same discipline as [[closure_record_claims_need_artifact_backing]] and
[[verify_handles_and_values_against_main_not_the_working_tree]]: a claim about the
repo is checked against the repo, whoever made it.

Related: [[reviewer_absence_claim_needs_orchestrator_own_live_reverification]] · [[reviewer_narration_is_not_pasted_evidence]]
