---
name: Testid enumeration copied from sibling's handle family, not this test's own call chain
description: a "reuses N pre-existing testids" closure-record claim can be derived from a sibling test's known handle family rather than the actual test-under-audit's page-object call chain — producing phantom + missing entries even when the final promotable conclusion happens to still hold
type: feedback
---

On #139 (ELITEA-1991, PR #604) the closure record claimed the extend-existing
test reused "14 pre-existing testids (12 own to `generate-skill-*`/`skill-*`
family + 2 shared `entity-card`/`entity-card-name`)". Tracing the test's
actual page-object call chain (every method it calls, one hop into each
method body) found the real dependency set differs on 5 of ~15 entries:

- **2 fabricated**: `skill-controls-menu-button`, `skill-delete-menu-item` —
  neither is touched anywhere; this test's cleanup is API-side
  (`skill_api.delete_skill()`), no UI overflow-menu interaction at all. These
  belong to the *sibling* ELITEA-1990 test's known handle family (which does
  exercise UI delete), not this one.
- **3 omitted real dependencies**: `generate-skill-modal` (touched by
  `open_modal()`'s `self.modal.wait_for(...)`, not just the `open_button`
  click), `generate-skill-back-button` (touched by `wait_for_review_form()`'s
  `self.back_button.wait_for(...)`, not just `approve_button`), and
  `skill-information-section` (touched by `SkillDetailPage.wait_for_page_load()`
  via an inline `page.get_by_test_id(...)` call — itself pre-existing tech
  debt, but still a real dependency).

Root cause pattern: when a case is an "extend-existing" gap-fill sibling of an
already-automated test in the same class/file, it's tempting to summarize
"reuses the same testids as the covering test" from memory of that sibling's
known handle family, rather than mechanically tracing *this* test's own
method calls one hop into each page-object method body (open_modal → clicks
open_button AND waits on modal; wait_for_review_form → waits on back_button
AND approve_button — both waits are dependencies even though only one
button is later clicked).

In this instance the CORRECTED set was independently re-verified fully
present on `main`, so the final "fully promotable" conclusion wasn't
falsified — but the record's own verification table (required to be "a
verified fact, not a copy of the AFS/implementer's claim") was still wrong,
which is the checklist-item-3 violation regardless of the lucky final answer.

**Rule going forward**: for an extend-existing sibling test, do NOT summarize
"same handles as test X" from memory — trace the NEW test's own method calls
into their page-object bodies (including `wait_for(...)` calls buried inside
helper methods, not just the field the test clicks directly) before writing
the closure record's testid row. This is the same discipline as
`testid_reference_check_must_include_page_object_fields.md`, applied at
closure-record time on a REUSED set instead of a NEWLY-added one.

**Recurrence — pure-omission variant, no fabrication (control-audit, issue
#143, ELITEA-1902, PR #606, 2026-07-18):** this delivery was otherwise
strong (correctly resolved two separate templated-testid families, a
genuinely tricky reviewer-caught regression-check correction verified
accurate on re-trace) — no evidence of copying a sibling's handle family.
Yet tracing the test's own call chain one hop into every method still
turned up 3 real dependencies missing from the closure record's 13-row
table: `agent-actions-menu-button`/`agent-actions-menu` (from
`export_agent_via_menu()` → `open_actions_menu()`, both composed via
`DotMenu.jsx`'s `${id}-menu-button`/`${id}-menu` off `id="agent-actions"`)
and `toolkit-open-button` (from `click_toolkit_open_in_new_tab()`, a plain
literal). All three independently confirmed already on `main` (zero diff
on every owning file), so the conclusion held — same "lucky final answer,
still a FAIL" shape as the original #139 finding, but this time the gap
wasn't sibling-copied, it was simply an incomplete sweep: the closure
record traced testids the PR/AFS narrative called out by name, not every
method the test transitively calls. **Sharper rule from this recurrence:**
when re-deriving item 3, don't start from "which testids does the PR
description mention" — grep every page-object method the test calls (one
hop into each body) for `LocatorDescriptor`/UPPER_CASE-constant usage,
independent of what the narrative highlights. Methods reached only
indirectly (opening a shared 3-dot menu before clicking a named menuitem,
hovering a card before clicking its open-in-new-tab button) are exactly
where a narrative-driven trace stops short.
