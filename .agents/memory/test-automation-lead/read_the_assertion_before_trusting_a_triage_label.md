---
name: Read the failing assertion before trusting a CI triage label
description: An auto-triage "flaky" verdict is a guess from job duration and context; the assertion text in the log names the real cause in one step
type: feedback
aliases: [flaky label, ai triage, planted failure, intentional failure, ci failure card, deterministic red]
tags: [area/ci, type/triage]
created: 2026-09-07
updated: 2026-09-07
---

## The lesson

`[Fix] CI Failure` cards carry an **AI Triage Analysis** block with a failure type and
confidence. It is a prior, not evidence — it reasons from job duration, recent commit
subjects and issue-similarity, and it has never read the assertion.

On #2016 it said `flaky (confidence: MEDIUM)` and recommended INVESTIGATE, reasoning from a
~66s job and an in-flight ELITEA-1886 flake repair. The actual log line:

```
tests/ui/smoke/test_ui_smoke.py:39: in test_page_loads
    assert False, "INTENTIONAL FAILURE: Testing webhook pipeline integration"
```

A deliberate probe (`30c2d1e08`, 2026-09-01), planted to exercise the failure→issue webhook
and never removed — deterministic, on both `main` and `automation/base`, red for 6 days.

**First move on any CI-failure card: pull the failed job log and read the assertion and its
message.** It is one `gh run view --job <id> --log` and it either names the cause outright or
tells you a reproduction is genuinely needed. Reproducing first, on a triage label's say-so,
spends a session confirming something the log already said.

## Tells that a red is planted, not flaky

- The assertion message says so (`INTENTIONAL`, `webhook`, `pipeline test`) — cheapest tell.
- `assert False` / a literal with no product call in the failing step.
- A sibling test in the same file passes — the platform is fine, the spec is not.
- `git log -S"<message>" origin/main -- <path>` names an author and a stated purpose.

A planted failure is neither flake nor product defect: no defect ticket, no `expect.soft()`,
no sanctioned-RED reasoning to attach it to. It is deleted, and the deletion is the fix.

## The second-order cost is the one to name in the closure record

While it sits there the suite is guaranteed-red, so a *real* regression in those specs is
indistinguishable from the plant. Say that explicitly — "the DEV-stable smoke signal was
masked for N days" is the part a human needs, not just "removed the line".

Related: [[a_product_change_is_not_a_product_bug]] · [[ci_red_check_base_for_an_existing_fix_first]] · [[environment_specific_framing_needs_a_local_reproduction_first]]
