# Test Case: Create agent — Instructions field alone does not enable Save (extension)

## Metadata
- **TMS ID**: ELITEA-1871
- **Linked Story**: EliteaAI/elitea-testing-public#175 (tracking issue, already `In Progress` on board #9 — no new sub-task filed)
- **Priority**: n/a — `extend-existing` (gap-fill record, not a fresh implementation)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids` branch → DEV backend)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips Keycloak login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: extend-existing — Rule-6 partial-overlap dedup against the merged
  test `test_create_agent_required_fields_validation`. That test already proves
  3 of the case's 4 distinct Save-enablement states (empty-disabled,
  name-only-disabled, both-enabled) but never fills Instructions and never
  tests description-only — exactly the case's title point
  ("instructions alone does not enable Save") and its Step 5 are net-new.

## Preconditions
- User must be logged in. On localhost this is already satisfied by the
  `auth_state` fixture, which skips the Keycloak login screen entirely via
  `VITE_DEV_TOKEN` (see `CLAUDE.md` § Critical Conventions).
- Create Agent page must be reachable at `/agents/create` (navigated to via
  `AgentsListPage.navigate_to_create()` in the covering test's existing
  Step 1).
- Both are already satisfied by the `page` fixture the covering test
  (`test_create_agent_required_fields_validation`) already receives and
  uses — this extension adds no new precondition and requires no new
  fixture setup; the two new steps run inside the same test, on the same
  already-loaded form.

## Test Data
### reuse-existing
None — this extension introduces no shared or stored data; every literal
used is a fresh inline string local to the test body.

### generate-per-test (in test setup, cleaned up in its own teardown)
- `"Any test instructions text"` — Instructions-field literal, passed
  inline to `fill_form(instructions=...)` at **NEW Step 3**. Never
  persisted (Save is never clicked anywhere in this test), no API call
  fires from filling the field, no teardown required.
- `"Some description"` — Description-field literal, passed inline to
  `fill_form(description=...)` at **NEW Step 5**. Same zero-persistence,
  zero-API, zero-teardown profile as above.
- `"autotest_partial"` — Name-field literal already established by the
  covering test's pre-existing Step 4/Step 6 (renumbered, otherwise
  unchanged) and reused verbatim by the surrounding, unmodified context
  the two new steps are inserted into. Carries the same
  generate-per-test / zero-cleanup profile: an inline `fill_form()`
  keyword argument that's never saved.

All three are literal strings passed directly as `fill_form()` keyword
arguments — no factory, no API seed call, no fixture. Setup cost is the
function call itself; teardown cost is zero because the form is never
submitted (Save's state is asserted, never clicked) and no agent record
is ever created.

### generate-shared-with-cleanup (shared across tests; cleaned up in suite teardown)
None — this extension shares no data across tests.

## Extension target

- **Covering test**: `automation/tests/ui/agents/test_agent_management.py:366-387`
  (`TestCreateAgent.test_create_agent_required_fields_validation`, class starts
  at line 267)
- **Covering AFS**: none — this test predates the AFS pipeline. Its two
  `@allure.issue` decorators (lines 363-364) point at
  `onetest-ai-tm-Elitea/tests/elitea-platform/agents/ELITEA-0136_agent-creation-field-validation.md`
  and `ELITEA-0145_agent-creation-ui-and-api.md`, not at an AFS file.
- **Covering TMS case**: none of the on-file ELITEA-1871 TMS case's own history —
  the covering test traces to ELITEA-0136/ELITEA-0145 instead. ELITEA-1871's own
  case file is `onetest-ai-tm-Elitea/tests/automated-full-regression-ui/agents/ELITEA-1871_create-agent-instructions-alone-does-not-enable-save.md`
  (`status: draft`, `execution_type: manual` — unwritten by this AFS; the
  orchestrator's back-write step owns that per `.agents/test-automation.yaml`).
- **Board task behind the covering test**: not tracked individually (the test
  predates the board-driven intake flow); ELITEA-1871's own board task is
  issue #175 (open, no `control:audited`/`testids:merged-to-main` labels yet —
  this AFS is the first pass at it).

## Behavioural overlap

Both ELITEA-1871 and the covering test assert the same underlying contract: the
Create Agent form's Save button is a pure function of `(name non-empty) AND
(description non-empty)` — nothing else gates it. The covering test proves 3 of
the state machine's cells live, right now (re-run in this session, see
Coverage Map): empty-fields → disabled (line 374-375), name-only → disabled
(377-380), both-filled → enabled (382-387). It never touches the Instructions
field at all, and never exercises description-only (it goes straight from
name-only to both-filled). ELITEA-1871's actual title point — "filling
Instructions alone does not enable Save" — is therefore untested today, and its
Step 5 (description-only → disabled) is a second gap. These two gaps are a small,
additive extension of the same test body, not new ground: same page, same form,
same `AgentFormPage.fill_form()` / `is_save_enabled()` machinery already in use.

**Live verification this session** (manual execution against
`http://localhost:5173/agents/create`, fresh page load, testid-driven via
Playwright MCP `page.getByTestId(...)`):

| Fields filled | Save state observed | Screenshot |
|---|---|---|
| Instructions only ("Any test instructions text") | disabled | `test-results/screenshots/ELITEA-1871-step3-instructions-only-save-disabled.png` |
| Name only ("autotest_1871_name") | disabled | (already covered live by the existing test; not re-screenshotted — see Coverage Map) |
| Description only ("autotest_1871_description"), Instructions still filled from the earlier step | disabled | `test-results/screenshots/ELITEA-1871-step5-description-only-save-disabled.png` |
| Name + Description + Instructions (all three) | **enabled** | `test-results/screenshots/ELITEA-1871-step6-both-filled-save-enabled.png` |

Console was clean (0 errors, 0 warnings) at every checkpoint. No product defect
found — live behavior matches the case's expected result at every step; this is
a coverage gap, not a bug.

**One self-inflicted false alarm ruled out during exploration** (documented per
the Synthetic Input Hygiene discipline, not filed): clearing the Name field via
two discrete `Control+a` then `Delete` key-press calls left a stray leading
character behind once (`autotest_1871_name` → `utotest_1871_name`), suggesting
select-all raced the field's controlled re-render between the two separate CDP
key events. Re-tested with Playwright's native `locator.clear()` (the exact
primitive `AgentFormPage.fill_form()` already uses in production code) in a
single call and it cleared cleanly every time. Not a product bug — a synthetic-input
sequencing artifact of my own two-step manual clear, ruled out per the
`playwright-testing` skill's pristine-repro gate before being considered further.

## Gap assertions

Insert two new `allure.step` blocks into
`test_create_agent_required_fields_validation` and renumber the two existing
post-empty-check steps. Target file:
`automation/tests/ui/agents/test_agent_management.py:366-387`.

**Why insert into the same test rather than add a sibling `test_*` method**
(declared improvisation — the dispatch brief flagged this boundary call
explicitly, per `.agents/role-overrides.md` § Declared-improvisation protocol):
the skill's own definition of `extend-existing` is "the implementer extends the
covering spec with the gap assertions" (test-case-analysis SKILL.md § Classify
findings) — i.e. append missing assertions to the existing spec, not spawn a
parallel one. This test is already a single continuous walk through the
Save-button state machine (empty → name-only → both-filled); Instructions-only
and description-only are two more cells of the *same* state machine, exercised
against the *same* form instance with the *same* `AgentFormPage` fixture setup
(navigate + `wait_for_form_load()`) the existing steps already pay for. A
sibling test would either re-navigate from scratch (duplicate, wasteful setup
for what is fundamentally the same assertion sequence) or awkwardly depend on
the first test's state (test-isolation violation). Two inserted steps plus a
renumber is not "near-rewrite" territory (skill's own extend-vs-fresh
boundary test) — the existing assertions, their wording, and their call shape
are untouched.

**Exact insertion** (new blocks in **bold**, unchanged blocks shown for
context/renumbering only):

```python
@allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0136_agent-creation-field-validation.md", "onetest-ai Test Case link")
@allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/agents/ELITEA-0145_agent-creation-ui-and-api.md", "onetest-ai Test Case link")
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1871_create-agent-instructions-alone-does-not-enable-save.md",
    "onetest-ai Test Case link (also covers ELITEA-1871 — instructions-alone and "
    "description-only sub-cases, see "
    "test-specs/agents/lextend_create-agent-instructions-alone-does-not-enable-save_ELITEA-1871.md)",
)
@pytest.mark.p1
def test_create_agent_required_fields_validation(self, page):
    """Save button should be disabled when required fields are empty.

    Also covers ELITEA-1871: Instructions filled alone, and Description filled
    alone, must each leave Save disabled — only Name AND Description together
    enable it.
    """
    with allure.step("Step 1 — Navigate to create agent page"):
        list_page = AgentsListPage(page)
        list_page.navigate_to_create()
        form_page = AgentFormPage(page)
        form_page.wait_for_form_load()

    with allure.step("Step 2 — Verify Save disabled with empty fields"):
        assert not form_page.is_save_enabled(), "Save should be disabled with empty required fields"

    # --- NEW: ELITEA-1871 case Steps 2-3 ---
    with allure.step("Step 3 — Fill only Instructions and verify Save still disabled"):
        form_page.fill_form(name="", description="", instructions="Any test instructions text")
        form_page.wait_for_form_validation()
        assert not form_page.is_save_enabled(), (
            "Save should be disabled when only Instructions is filled (name and description empty)"
        )

    with allure.step("Step 4 — Fill only name and verify Save still disabled"):
        form_page.fill_form(name="autotest_partial", description="")
        form_page.wait_for_form_validation()
        assert not form_page.is_save_enabled(), "Save should be disabled without description"

    # --- NEW: ELITEA-1871 case Step 5 ---
    with allure.step("Step 5 — Clear name, fill only Description, verify Save still disabled"):
        form_page.fill_form(name="", description="Some description")
        form_page.wait_for_form_validation()
        assert not form_page.is_save_enabled(), (
            "Save should be disabled when only Description is filled (name empty)"
        )

    with allure.step("Step 6 — Fill both fields and verify Save enabled"):
        form_page.fill_form(name="autotest_partial", description="Some description")
        form_page.wait_for_form_validation()
        assert form_page.is_save_enabled(), (
            "Save should be enabled when both name and description are filled"
        )
```

Notes for the implementer:
- `fill_form(name="", description="", instructions=...)` is safe at Step 3:
  `AgentFormPage.fill_form()` (`automation/pages/agent_form_page.py:266-321`)
  always clicks+clears+`press_sequentially()`s name and description (typing an
  empty string after `clear()` is a no-op, fields end up empty), and only
  touches Instructions/Welcome-message when the argument is truthy
  (`if instructions:` at line 304) — so Step 3 leaves the form in exactly
  "Instructions filled, Name/Description empty" with no extra plumbing needed.
- Step 4's `fill_form(name="autotest_partial", description="")` does **not**
  clear Instructions (the `if instructions:` guard at line 304 skips the block
  when the call omits the arg / passes `""`), so Instructions stays filled with
  "Any test instructions text" through Steps 4-6 — matches the live
  verification above (I kept Instructions filled through description-only too,
  confirming it never contributes regardless of what else is filled).
- Step 5's `fill_form(name="", description="Some description")` clears Name
  (same no-op-empty-string mechanism as Step 3) while setting Description —
  this is the "Clear Name, fill Description only" the case asks for.
- Convention check performed before proposing this shape: no neighbouring test
  in this file stacks 3 `@allure.issue` decorators, but the two-decorator
  pattern (one TMS-case link + one gap-fill note) is already established at
  `test_export_agent_with_attached_skills.py:73-77` (ELITEA-1896 extension) —
  a third decorator repeating the same `"onetest-ai Test Case link"` label
  text, differing only in URL and note, is the natural extension of that
  precedent rather than an invented shape.

## Coverage Map

### Axis 1 — Case element → Coverage
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Step 1: Navigate to Create Agent page | Form displayed, all fields empty | Covering test, Step 1 (`:368-372`) | `list_page.navigate_to_create()` + `form_page.wait_for_form_load()` | already-covered |
| Steps 2-3: Leave Name/Description empty, fill only Instructions; verify Save disabled | Instructions accepts input; Save remains disabled | **NEW Step 3** (see § Gap assertions) | `fill_form(name="", description="", instructions=...)`; `assert not is_save_enabled()` | asserted *(net-new — live-verified this session, disabled)* |
| Step 4: Fill Name only; verify Save still disabled | Name filled; Save disabled | Covering test, Step 3→renumbered Step 4 (`:377-380`) | `fill_form(name="autotest_partial", description="")`; `assert not is_save_enabled()` | already-covered |
| Step 5: Clear Name, fill Description only; verify Save still disabled | Description filled; Save disabled | **NEW Step 5** (see § Gap assertions) | `fill_form(name="", description="Some description")`; `assert not is_save_enabled()` | asserted *(net-new — live-verified this session, disabled)* |
| Step 6: Fill both Name and Description; verify Save enabled | Save becomes enabled | Covering test, Step 4→renumbered Step 6 (`:382-387`) | `fill_form(name="autotest_partial", description="Some description")`; `assert is_save_enabled()` | already-covered |
| Pass criteria: all steps complete without error; Save enables only when both required fields filled | No errors; correct enablement gating throughout | Covering test end-to-end (with the two new steps inserted) | Full walk through empty → instructions-only → name-only → description-only → both-filled | asserted (composite of the rows above) |

### Axis 2 — Observables asserted beyond the case
| Observable | Reason |
|---|---|
| Instructions value persists unaffected across the Name-only and Description-only checks (not cleared, not re-typed) | Confirms Instructions truly never participates in the enablement gate, regardless of what other fields hold at the time — stronger than testing Instructions in isolation only |
| Zero console errors/warnings across all 4 form-state transitions | Silent JS errors during MUI debounced validation would be the kind of bug a pure DOM-attribute check could miss |
| Native `Locator.clear()` behavior cross-checked against a manual `Control+a`+`Delete` sequence (see § Behavioural overlap) | Ruled out a synthetic-input artifact before it could be mis-filed as a product defect — documents why the extension code below uses `fill_form()`'s built-in `clear()`, not raw key sequences |

## Known Defects
None. Live product behavior matches the case's expected result at every one of
the 4 form-fill states tested (empty / instructions-only / name-only /
description-only / both-filled — 5 states across the 4 case steps that assert
Save's enabled/disabled value). No `defect-found` classification applies; no
tracker write needed beyond the existing tracking issue EliteaAI/elitea-testing-public#175
(already open, `In Progress`, no re-filing required per dispatch brief).

## Cleanup
None — this AFS specs an extension to an existing test that creates no agent
(it only exercises client-side form-validation state and never clicks Save),
same as the original covering test. No entities are created; nothing to tear
down.

## Concrete Handles (discovered during exploration)

All four elements confirmed live against `http://localhost:5173/agents/create`
via `document.querySelector('[data-testid="..."]')` in this session — every
handle below is already in `AgentFormPage` and needs no new testid work.

| Element | Testid (LocatorDescriptor field) | Provenance | Notes |
|---|---|---|---|
| Name input | `agent-name-input` (`AgentFormPage.name_input`) | on-main ✓ (confirmed live in DOM, `<input>`, `disabled=false`) | Existing field, reused as-is |
| Description input | `agent-description-input` (`AgentFormPage.description_input`) | on-main ✓ (confirmed live, `<textarea>`, `disabled=false`) | Existing field, reused as-is |
| Instructions input | `agent-instructions-input` (`AgentFormPage.instructions_input`) | on-main ✓ (confirmed live, `<textarea>`, `disabled=false`) | Existing field, reused as-is — this is the field the case's title point hinges on |
| Save button | `agent-save-button` (`AgentFormPage.save_button`) | on-main ✓ (confirmed live, `<button>`, `disabled=true` initially, flips to `false` once Name+Description are both non-empty) | State read via `is_save_enabled()` → `self.save_button.is_enabled()`, not a `data-*` state filter — the button's native `disabled` attribute IS the state signal here, no separate `data-*` attribute needed |

No `testid needed:` gaps — every element the case touches already has a
class-level `LocatorDescriptor(testid=...)` field in `AgentFormPage`, and all
four were re-verified against the live DOM this session (not assumed from the
dispatch brief's grep).

## Network Behavior
None to note — the extension only exercises client-side MUI form-validation
state (Save button's `disabled` attribute driven by React state), no network
request fires from filling fields alone. (Save was never clicked in this
exploration; clicking it is out of scope for both the original case and this
extension.)

## Blocked Steps
None.

## Automation Hints
- Framework: pytest + Playwright, confirmed from the existing test file.
- Page object: `automation/pages/agent_form_page.py` — `fill_form()`,
  `is_save_enabled()`, `wait_for_form_load()`, `wait_for_form_validation()` all
  already exist and need no changes; the extension is pure test-body insertion,
  no new page-object methods.
- Wait strategy: reuse `form_page.wait_for_form_validation()` after each
  `fill_form()` call (already the pattern in the covering test) — it wraps
  `wait_for_network()` + the ~500ms MUI debounce; no new wait primitive needed.
