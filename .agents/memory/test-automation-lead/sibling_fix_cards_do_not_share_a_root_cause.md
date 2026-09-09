---
name: Sibling [FIX] cards from one CI run do not share a root cause
description: Check the failing job's own pass/fail spread before inheriting a sibling card's verdict
type: feedback
aliases: [sibling fix card, same CI run, mass failure, outage transfer, 8 of 10 jobs failed]
tags: [area/triage, type/lesson]
created: 2026-09-09
updated: 2026-09-09
---

## The trap

A bad CI run files a whole family of `[FIX]` cards at once (run 34331579791 → #2074–#2084,
8 of 10 jobs failed). Once ONE of them is root-caused — and written into
`.agents/testing.md` as a platform-wide outage — every sibling looks pre-solved.
It is the most inviting shortcut on the board, and it is wrong by default.

## The 30-second check that decides it

Read the **failing job's own log**, and look at the tests **around** the failure:

- Neighbours on both sides FAILED → plausibly the shared outage window.
- Neighbours PASSED → the outage did not reach this test. It is a real, separate defect.

On #2076 the `pipelines` job lost 3 of ~30 tests and the tests immediately before and after
the target passed. The aria snapshot showed the app rendering normally — no branded 500 page.
It was a genuine test defect (an inert wait) that the outage narrative would have buried.

## Corollary

The reverse also holds: my own confident triage sentence, once posted, is what the next
session inherits. On #2076 I posted "chat frozen at `Fetching keys & creds …` = the run hung" —
the analyst then measured the placeholder **rotating every 2.0 s** and showed that string is just
carousel frame 4, i.e. the run had not STARTED. Write triage so it can be falsified: quote the
observation, name the inference separately, and say which is which.

Related: [[a_fix_card_can_have_no_work_in_it]] · [[a_product_change_is_not_a_product_bug]] · [[the_second_error_line_in_a_ci_log_is_often_the_real_cause]]
