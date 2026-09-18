---
name: EL-6532 made the SDK serialize tool results as JSON — every oracle captured before 2026-09-07 as a Python repr / prose is a drift candidate, and setup ERRORs from the same family are never carded by intake
description: One SDK commit (~45 methods, 15 toolkits) silently invalidates captured tool_output shapes; a [FIX] card names one param, the sibling params fail as setup ERRORs that the intake pipeline does not file
type: feedback
aliases: [EL-6532, fe3377278, tool_output json drift, list_projects Found N projects, space_key field required, setup ERROR not carded, toolkit oracle drift]
tags: [area/toolkits, area/triage, type/lesson]
created: 2026-09-18
updated: 2026-09-18
---

## The finding (#2362, ELITEA-1140, 2026-09-18)

EliteaAI/elitea-sdk@fe3377278 (EL-6532, PR #598, 2026-09-07 — "serialize tool results as JSON
instead of a Python repr") touched ~45 toolkit methods across 15 toolkits. Jira `list_projects`
went from `"Found <n> projects:\n[{'id': …}]"` to a bare pretty-printed JSON array. The oracle
captured 2026-08-27 (`^Found \d+ projects:`) rejected a **successful** call — a red that reads as
"Jira connectivity" in the intake prose and is nothing of the kind.

**The tell that costs 10 seconds:** the assertion message PASTES the real `tool_output`. If what
it pastes is a healthy payload, the oracle is stale, not the product — go straight to re-capture.

## Two things the card did NOT tell you

1. **Sibling params fail as setup ERRORs, and the intake pipeline files nothing for ERROR
   outcomes** — only FAILED. In the same run `[confluence]` ERROR'd at toolkit create
   (`400 settings.space_key Field required`; `toolkit_factories.py` still posts `"space"`) and no
   card existed until I filed #2365. After any `[FIX]` card, grep the job log for `ERROR` at
   setup on the same file — the same drift family is usually there, uncarded.
2. **Other toolkits' captured shapes are drift candidates too.** github's/confluence's samples
   were re-verified only in that they still pass; any oracle captured pre-2026-09-07 as a repr
   is suspect the next time its param goes red.

## What the repair must contain (and did)

- Re-CAPTURE the success frame on the live system (never infer from the changelog — capture
  is the authority; the commit is the *explanation*).
- Capture the FAILURE shape honestly (bogus API key → real rejection). For Jira the SDK
  validates credentials at toolkit **construction**, so no `list_projects` frame is emitted at
  all — Tier 1 (0 frames) is the rejection guarantee, the pattern is defence in depth.
- Pin the OLD shape as *no longer a success* — no alternation, or the next flip-flop is invisible.
- Walk every config row: a pattern that now overlaps a sibling's shape is fine only if the
  Tier-1 tool+toolkit filter disambiguates, and the overlap must be **test-enforced**, not
  docstring-documented (reviewer NIT that turned into an assertion).
- Declare narrowings (`[]` now FAILED where `Found 0 projects:` passed) in config + AFS.

Related: [[capture_the_payload_never_infer_it]] · [[removing_a_false_red_guard_can_create_a_false_green]] ·
[[fix_card_is_generated_from_ONE_attempt_diff_the_attempts_first]]
