---
name: AgentFormPage.fill_form() press_sequentially timeout ceiling
description: fill_form() types instructions/description/name via press_sequentially(delay=80ms/char) against a 10s default Playwright action timeout — long planted-marker strings can silently time out and look like a product hang
type: feedback
---

`AgentFormPage.fill_form()` (and the equivalent `SkillFormPage.fill_form()`)
fills the Name/Description/Instructions fields via
`locator.press_sequentially(text, delay=80)` — required because MUI/React
form fields don't fire `onChange` on Playwright's `fill()` (see
`.claude/rules/mui-patterns.md` § MUI Form Fields). Each `press_sequentially`
call has Playwright's **default 10s action timeout**, so any field text over
roughly **~120 characters** (120 * 80ms = 9.6s, no margin) risks a
`TimeoutError` that looks exactly like an environment/product hang but is
purely an automation-fixture-string-length mismatch.

Hit this on ELITEA-1894 (export-agent-no-nested-dependencies): the AFS's
"used in this run" instructions string (~180 chars, embedding a verbatim
marker + explanatory prose) timed out at ~14.4s of typing. Fix: shorten the
instructions text while keeping any load-bearing marker literal intact
(e.g. `ELITEA_1894_INSTR_MARKER`) — the assertion only needs the marker
verbatim, not the exact prose length.

`fill_form()` itself was correctly left untouched (16 callers across the
suite — additive-only discipline, not a per-case patch target). If a case
genuinely needs a long planted-marker string (e.g. proving full-verbatim
embedding, not just presence), either:
- keep the total field text under ~120 chars, or
- extend `fill_form()`/the underlying locator calls with an explicit,
  backward-compatible `timeout` kwarg (default unchanged) rather than
  hardcoding a workaround per test — that's additive and reusable for the
  next case that needs it.

Any future case that plants a marker in an Agent's or Skill's
name/description/instructions field via the create/edit form should budget
for this ceiling up front.
