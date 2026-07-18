---
name: extend-existing means insert into same test, not a sibling test method
description: When Rule-6 partial overlap classifies a case as extend-existing, the default shape is inserting the gap assertions as new steps into the covering test's own body (renumbering as needed), not authoring a parallel sibling test() method — confirmed via ELITEA-1871's lextend AFS
type: feedback
---

## The situation

ELITEA-1871 ("Create agent — Instructions alone does not enable Save") was
dispatched with an explicit open question: the covering test
(`test_create_agent_required_fields_validation`, `test_agent_management.py:366-387`)
already proved 3 of 4 Save-enablement states (empty-disabled, name-only-disabled,
both-enabled) but never touched Instructions and never isolated description-only.
The dispatch brief floated two options and left the boundary call to the analyst:
(a) a fresh `lextend_*.md` AFS describing insertion of new steps into the SAME
test, or (b) "a new sibling `test()` method appended to the same class, tagged
for ELITEA-1871."

## The reasoning that resolved it

`test-case-analysis` SKILL.md's own definition of `extend-existing` is: "Don't
write a fresh `.spec.ts`; the implementer **extends the covering spec** with the
gap assertions." That phrase — "extends the covering spec" — means append
missing assertions to the *existing* spec/test, not spawn a second one next to
it. A sibling test method is closer in spirit to `ready-for-automation` (new
test authored fresh) than to `extend-existing` (existing test grows).

The practical tell, useful for future boundary calls: is the covering test
already walking a **single continuous state machine** that the case's missing
assertions are just more cells of? Here, the covering test is exactly that — a
progressive fill-and-check sequence (empty → name-only → both-filled) using the
same `AgentFormPage` fixture and the same `is_save_enabled()` polling idiom.
Instructions-only and description-only are two more cells of that same machine,
not a different flow. Inserting them:

- reuses the one `navigate_to_create()` + `wait_for_form_load()` setup the
  existing steps already pay for (a sibling method would either duplicate that
  setup or, worse, depend on the first test's leftover state — a test-isolation
  violation);
- keeps the "small number of assertions missing" character required for
  `extend-existing` (SKILL.md: "if the gap is large enough that the extension
  would be a near-rewrite of the covering spec, treat as `ready-for-automation`
  instead" — 2 inserted `allure.step` blocks + renumbering 2 existing labels is
  nowhere near that threshold).

## The reusable check

When extend-existing's gap assertions are more test *states* of an existing
state-machine-shaped test (form validation progressions, wizard steps, toggle
sequences) rather than a wholly different flow, prefer inserting into the
existing test body and renumbering, over drafting a parallel test method — even
when the dispatch brief presents both as equally live options. Reserve the
sibling-method shape for gaps that are a genuinely separate scenario sharing
only setup (e.g., a different entry point, a different data precondition) —
where duplicated setup is the honest cost of test independence, not avoidable
bloat.

See `test-specs/agents/lextend_create-agent-instructions-alone-does-not-enable-save_ELITEA-1871.md`
§ Gap assertions for the full worked declared-improvisation writeup.
