---
name: Count vs assistant-count getter unit mismatch
description: SupportAssistantPage.get_message_count() (total, both roles) vs get_assistant_message_count() (assistant-only) are easy to cross-compare by mistake; a soft-check mixing the two under-detects by ~2x
type: feedback
---

`automation/pages/support_assistant_page.py` exposes two counters that look
interchangeable but aren't:

- `get_message_count()` — ALL `.elitea-assistant-message-wrapper` (user + assistant)
- `get_assistant_message_count()` — assistant-only wrappers (`--assistant` class,
  falls back to Copy-to-clipboard button count)

Since a normal exchange is 1 user + 1 assistant message, total ≈ 2×assistant-only.
Any check comparing a TOTAL count captured at one point against an ASSISTANT-ONLY
count captured at another point (`restored_message_count < count_before` style,
where `restored_message_count` comes from `get_message_count()` and `count_before`
from `get_assistant_message_count()`) will only fire once the assistant-only side
alone crosses whatever threshold the total side is bounded by — i.e. it engages
roughly twice as late as intended, and can silently fail to catch the exact
condition it was written to detect.

Found in PR #608 (ELITEA-1799 Step 6, `test_support_assistant_smoke.py:271`): a
soft-check meant to detect GH#607's conversation-truncation defect used this
mismatched pair and, per the analyst's own manually-reproduced numbers (100 total
truncated wrappers vs 48 assistant-only pre-count that same run), would NOT have
fired against the confirmed real repro. Only a same-unit comparison (total vs
total, or assistant vs assistant, both captured at consistent points) actually
tracks the defect's signature. When reviewing or writing an assertion that spans
these two getters, verify both operands come from the same getter before trusting
the comparison — do the arithmetic with real observed numbers, don't assume "count
went down" implies "count went down for the right reason."

**R2 verification (same PR, fix-only round):** implementer added a `total_count_before
= support_page.get_message_count()` baseline in Step 2 (captured after the send/
response, so it's the "102" side of the analyst's numbers) and repointed both the
Step 4-5 reset-check and the Step 6 EFS-3 check at it — total-vs-total throughout.
Re-derived by hand against the analyst's 100/102/100 sequence: `100 < 102` now
correctly fires. Independently re-ran the merged test (fresh `git worktree`,
symlinked `.env.test` in) — PASSED, consistent with the implementer's claimed
GREEN 3/3. R2 verdict: APPROVED.
