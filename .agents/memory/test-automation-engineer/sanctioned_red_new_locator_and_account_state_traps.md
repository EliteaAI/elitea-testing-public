---
name: Sanctioned-RED known-defect assertions — new-locator trap and account-state-dependent reproduction
description: Three traps hit while implementing/fixing ELITEA-1799's GH#607 known-defect assertion — (1) a dispatch-suggested expect.soft(page.get_by_text(...)) implementation is itself a new non-testid locator addition, which this project's mechanical review-gate check flags regardless of "third-party widget scope exception" framing; (2) a sanctioned-RED assertion tied to a volume/history-dependent defect (not a pure logic/UI-state bug) may not reproduce RED at all when the shared account's state doesn't currently meet the defect's precondition — report this honestly rather than assuming the dispatch's expected outcome; (3) SupportAssistantPage.get_message_count() (total) vs get_assistant_message_count() (assistant-only) are easy to cross-compare by mistake in a soft-check, silently under-detecting by ~2x.
type: feedback
---

## What happened (ELITEA-1799, PR #608)

Dispatched to add a sanctioned-RED assertion for GH#607 (Support Assistant
conversation restore truncates to the oldest 100 message groups). The
dispatch's own suggested implementation was
`expect.soft(page.get_by_text(...)).to_be_visible()`.

### Trap 1 — a "just reuse existing handles" instruction can still smuggle in a new locator

The widget's existing handles (CSS/ARIA selectors, documented in the AFS's
Concrete Handles section) are a **permanent scope exception** to this
project's testid-only locator policy — because it's a third-party npm
package with no first-party JSX to attach a `data-testid` to. But that
exception covers *reusing already-documented* handles, not *authoring new
ones*. `page.get_by_text(...)` for a never-before-referenced string is a
brand-new locator, full stop — and `.agents/workflow.md` § Review gates has
a **mechanical** check for exactly this: `grep` the PR diff for added
`get_by_role|get_by_label|get_by_text|page.locator|.locator(` lines; each
hit must resolve to a `[data-testid=` selector, no exceptions carved out by
"the widget already has non-testid tech debt." Adding one more raw locator,
even to a file that already has several, is still `CHANGES_REQUESTED`.

**Fix:** when the value being compared is a plain string/int (not something
that needs live visibility polling), use the page object's existing
*getter methods* (`get_message_count()`, `get_last_message_text()`, etc.)
and compare their return values with plain Python `!=`/`<` — no Locator
construction at all. For the "soft assert but the values aren't
Page/Locator/APIResponse" shape, this project already has an established
pattern: a `soft_failures = []` list appended to under a `# Known defect:
#N` comment, with a final `if soft_failures: pytest.fail(...)` — see
`test_fork_agent_to_different_project.py` (#570) and
`test_skill_agent_interaction.py` (#38). Reach for that before reaching for
`expect.soft()` any time the comparison isn't natively a Locator assertion.

### Trap 2 — a volume/history-dependent defect's "sanctioned RED" isn't guaranteed at every instant

GH#607 only manifests once a conversation has accumulated >~100 message
groups. The AFS's analyst pass observed this on a conversation with 218
groups. But `test_new_chat_creates_fresh_session` and
`test_history_restore_and_continue` are the *only* two tests in the file
that call `start_new_chat()` — and every run of either test **archives
whatever conversation was active and starts a fresh one**, so the specific
conversation this test's own Step 6 checks (`select_history_session(index=0)`
— the just-archived one) is, by construction, always small/fresh relative
to its own single-run lifecycle. Verified via `--log-cli-level=INFO`: the
account's active conversation was observed growing by exactly +1 assistant
message per run (not resetting to a brand-new tiny conversation each time
either — same "active" conversation persists server-side across pytest
invocations), nowhere near the ~100 threshold, even after several
consecutive runs in one sitting.

This is a materially different defect shape than the deterministic
UI-state bugs this project usually soft-asserts (#585/#551/#526's
"clearing search after zero results" — reproduces identically every single
time, no dependency on incidental data volume). `.agents/testing.md` §
Merge gate's Sanctioned-RED bar ("3/3 identical failures IS its
deterministic gate") assumes exactly that kind of pure, stateless
reproduction. A volume-dependent defect can be added as a soft-assert
(matches the project's "keep it visible in the suite" philosophy, and has
precedent via #38's *intermittent* — as opposed to *volume-gated* — known
defect), but its RED-ness is NOT guaranteed on any given run, and that must
be reported honestly rather than assumed.

### Trap 3 (found in review, fixed in R1) — get_message_count() vs get_assistant_message_count() cross-comparison

`SupportAssistantPage` exposes two counters that look interchangeable but
aren't: `get_message_count()` is TOTAL (`.elitea-assistant-message-wrapper`,
user + assistant), `get_assistant_message_count()` is ASSISTANT-ONLY (the
`--assistant` variant, falling back to Copy-to-clipboard button count).
Since a normal exchange is 1 user + 1 assistant message, total ≈
2×assistant-only — so a check that captures one baseline via the
assistant-only getter and later compares it against a value read via the
total getter (`restored_message_count < count_before` where
`restored_message_count` is total and `count_before` is assistant-only)
engages roughly twice as late as intended, and can silently fail to catch
the exact condition it exists to detect. A fresh qa-engineer review caught
this in my own Step 6 check by running the analyst's own repro numbers
through it (100 total truncated wrappers vs 48 assistant-only messages that
run: `100 < 48` is `False` — would not have fired on the confirmed real
repro). Fix: capture a baseline with the SAME getter you'll compare
against later — in this case, capture `total_count_before =
get_message_count()` at the same point `count_before =
get_assistant_message_count()` is captured, and use `total_count_before`
for every later comparison against another `get_message_count()` result.
See `.agents/memory/qa-engineer/count_vs_assistant_count_getter_unit_mismatch.md`
for the qa-engineer-side writeup of the same finding.

## Durable rule for future implementers

1. When asked to soft-assert a known defect, check whether the comparison
   is natively a Locator/Page/APIResponse assertion (`expect.soft()`
   applies) or a plain value comparison (str/int/list — use the
   `soft_failures` list + final `pytest.fail()` pattern instead). Never
   introduce a new raw locator just to force-fit `expect.soft()`'s API
   shape — that's a policy violation regardless of any existing-tech-debt
   exception on the same widget/page.
2. Before shipping a "this will reproduce RED" claim for a known defect
   tied to accumulated state/volume (not a pure logic/UI bug), actually run
   it and look at the result. If it's GREEN because the precondition isn't
   currently met, say so explicitly (in the AFS amendment, PR body, and Run
   Report) rather than reporting the dispatch's anticipated outcome as if
   observed. A forward-looking regression net that isn't currently red is a
   legitimate and useful thing to ship — but only if labeled as such.
3. When a page object exposes multiple counters/getters that measure
   related-but-different things (total vs. a subset, e.g.
   `get_message_count()` vs `get_assistant_message_count()`), verify every
   operand of a comparison came from the SAME getter before trusting the
   check — do the arithmetic with real observed numbers from a live run,
   don't assume "count went down" implies "count went down for the reason
   the assertion claims."
