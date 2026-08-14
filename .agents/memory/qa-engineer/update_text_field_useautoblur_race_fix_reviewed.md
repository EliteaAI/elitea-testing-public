---
name: update_text_field useAutoBlur race fix — review verified
description: Reviewed ELITEA-2614 fix-only round (51ca89ac) — read-back+retry closes a real 10ms auto-blur typing race in AgentFormPage.update_text_field(); shared-file regression protocol was followed correctly
type: feedback
---

## What was reviewed (commit `51ca89ac`, `tests/batch-skills-remaining-w3`)

`AgentFormPage.update_text_field()` (Name/Description/Instructions/Welcome
message on the agent DETAIL/edit page) types via `field.click()` +
`Ctrl/Cmd+A` + `field.type(value)` — instant, no inter-keystroke delay. The
shared `StyledInputEnhancer`/`InputBase` wrapper (`enableAutoBlur=true`
default, `src/hooks/useAutoBlur.jsx`) restarts a **10ms** blur+refocus timer
on every keystroke. On an occasional slow event-loop tick that timer can
fire mid-typing even at instant speed, corrupting the final value (a tail
fragment of the OLD text gets duplicated back in). Observed live 1/3 runs
(ELITEA-2614 Step 23's Description-persistence assertion).

**Fix:** keep instant typing (a real per-keystroke delay, e.g.
`press_sequentially(delay=20)` matching `fill_form()`'s own CREATE-form
pattern, was tried and reliably regressed a DIFFERENT caller —
`test_import_agent_recreates_skills_with_new_ids.py`'s console-error
assertion, 2/2 runs, a real "Maximum update depth exceeded" React warning,
because a delay ≥10ms lets the timer fire BETWEEN every keystroke instead of
only once after typing stops). Add a defensive `field.input_value()`
read-back after typing; on mismatch, log + retype once; hard-assert if the
second attempt also mismatches.

## Review verdict: APPROVED (no blocking findings)

- Read-back+retry is a genuine mechanism, not a disguised sleep — no
  `wait_for_timeout`/`sleep` anywhere in the diff.
- Enumerated every caller of `update_text_field`/`update_name`/
  `update_description`/`update_welcome_message` in the UI repo (grep for the
  method names across `tests/`) — none intentionally types an
  invalid/overlong value this new hard-assert could newly break. Note:
  `pipeline_form_page.py` has its OWN separate `update_text_field` — not
  touched by this diff, no cross-file risk.
- Shared-file regression protocol (`test-automation-implementation` Hard
  Rule 11 / § Additive-only on shared-caller files → "if the change
  genuinely cannot be additive") was followed correctly: implementer
  enumerated all ≥3 merged callers, re-ran them, and named verdicts in the
  commit message (this was a direct trunk push, not a PR — an accepted
  "post-merge trunk fix for the wave's gate" pattern already established
  elsewhere in this batch, e.g. the ELITEA-2595/2596/2598 fix-only rounds).
- Mechanical locator-policy grep on the cumulative diff
  (`origin/automation/base...origin/tests/batch-skills-remaining-w3` for
  `agent_form_page.py`) was 0 hits — no new non-testid handles; the file's
  pre-existing `fallback=` lambdas (lines 25-46) predate this diff, tracked
  tech debt (#25/#42), untouched here.

## Reusable lesson for future shared-page-object timing-race fixes

When a race is real but rare (not eliminated by the "obvious" fix of adding
a delay), a read-back-and-retry-once + hard-assert-on-second-failure is the
right shape: it doesn't mask a real defect (hard fails if genuinely broken),
doesn't add a sleep, and is cheap to verify statically — check the retry
actually re-invokes the SAME real action (not a weakened check) and that the
final assert isn't softened. Always grep every merged caller of the method
before approving a body-modifying (non-additive) change to a shared
page-object method — the caller list is exactly where a hidden
"intentionally-invalid-value" test would live and break silently.
