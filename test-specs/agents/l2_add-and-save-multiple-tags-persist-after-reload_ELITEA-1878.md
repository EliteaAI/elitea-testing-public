# Test Case: Add and save multiple tags — both persist after reload

## Metadata
- **TMS ID**: ELITEA-1878
- **Linked Story**: none
- **Priority**: medium (`l2`)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI
  `automation/testids` branch → DEV backend), project `Private` /
  `${ELITEA_PROJECT_ID}` (project id `399` on this run)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips
  login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot (batch `agents-batch1-1277`,
  cluster dispatch with ELITEA-1879 — one live session, per-case execution)
- **Status**: `ready-for-automation` — case executed end-to-end live against
  `http://localhost:5173` (agent id `5189`, `manual_test_agent`), all 5
  steps verified, **no functional defect**. One **testid gap** on the Agent
  Tags field (input + chips + chip-delete icon) — the shared `TagEditor`/
  `AutoCompleteDropDown` component already threads `inputTestId`/
  `chipTestId`/`chipDeleteTestId` for the Pipeline form
  (`pipeline_form_page.py`'s `pipeline-tags-input`/`pipeline-tags-chip`),
  but the Agent branch of `ApplicationEditForm.jsx` intentionally left these
  `undefined` per canon #511 scope discipline ("no case exercises Agent's
  Tags yet" — see that file's own comment, lines 176-182). This case (+
  ELITEA-1879) is exactly the case that closes that gap — see Concrete
  Handles below for the exact prop names and recommended dynamic-testid
  naming.

## Preconditions

- User is logged in (on localhost, `auth_state` fixture skips login).
- An existing agent is available with an initially-empty Tags field (or the
  test seeds/asserts a known starting tag set — see Test Data).

**Implementation guidance:** follow the ELITEA-1873 precedent (same surface,
same PUT-persists pattern) — use a **dedicated, disposable agent** created
via `AgentAPI.create_agent_full()` (`reasoning_effort: "none"`, no
`temperature`, per the open `#524` 400 workaround already used by every
disposable-agent fixture in this area), deleted in a `finally` block. Do
**not** reuse the shared `manual_test_agent` (id `5189`) for the automated
test — it was used only for this analyst's live exploration (see Cleanup
below; tags added during exploration were removed again before handoff, so
the shared fixture is back to zero tags).

## Test Data

### Literal values
| Field | Value |
|-------|-------|
| Tag 1 | `regression_test` |
| Tag 2 | `automation` |

## Test Steps

1. Navigate to an agent detail page.
   - **Verify — PASSES.** Agent detail page loads; Tags field renders as an
     MUI `Autocomplete` combobox (accessible name "Tags"), initially empty
     (no chips) on a fresh agent.
2. Add tag "regression_test" and tag "automation" (type into the Tags
   input, press Enter to commit each as a chip).
   - **Verify — PASSES.** Each committed tag renders as a chip
     (`role="button"`, accessible name = the tag text, with a delete `img`
     icon inside) immediately after Enter — confirmed live for both tags,
     no debounce/delay needed (this is pure client-side Formik state before
     Save, same as the Pipeline Tags field).
3. Click Save.
   - **Verify — PASSES.** `agent-save-button` click fires
     `PUT /api/v2/elitea_core/application/prompt_lib/{projectId}/{agentId}`
     → `201 Created`. No console errors (0 errors, 0 warnings on the
     `browser_console_messages` check after save).
4. Reload the page.
   - **Verify — PASSES.** Page reloads (fresh navigation), Tags field
     re-renders from the freshly-fetched agent data
     (`GET .../application/prompt_lib/{projectId}/{agentId}`).
5. Verify both "regression_test" and "automation" tags are shown in the Tags
   field.
   - **Verify — PASSES.** Both tag chips are present, in the same order
     they were added (`regression_test` first, `automation` second) —
     confirmed via the accessibility snapshot post-reload
     (`test-results/screenshots/ELITEA-1878-step-05-tags-persist-after-reload.png`).

## Expected Results

After reload, both `regression_test` and `automation` tags are present as
chips in the Tags field. (Note: the case's own "Expected Final State"
section literally says "both 'regression-test' and 'automation'" — a hyphen
vs the Test Data table's underscore `regression_test`. This is a case-text
typo, not a product behavior difference; the automated assertion uses the
Test Data table's literal value `regression_test`, matching what was
actually typed/verified live. Not filed — too trivial for its own
clarification ticket, noted here so the implementer doesn't "fix" the
assertion to the hyphenated form.)

## Coverage Map

### Axis 1 — case element → covered by → disposition

| Case element | Expected result | Covered by (steps above) | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | Session active | `auth_state` fixture (localhost `VITE_DEV_TOKEN`) | n/a (fixture-level) | covered |
| Precondition: existing agent available | Agent detail page reachable | Test-data setup (`create_agent_full()`) | agent created, id captured | covered |
| Step 1: navigate to agent detail page | Page loads | Step 1 | Tags combobox visible, empty | covered |
| Step 2: add tag "regression_test" and tag "automation" | Both appear as chips in Tags field | Step 2 | chip with accessible name "regression_test" visible; chip with accessible name "automation" visible | covered |
| Step 3: click Save | Save completes successfully | Step 3 | PUT to `application/prompt_lib/{proj}/{id}` returns `201` | covered |
| Step 4: reload the page | Page reloads | Step 4 | fresh navigation + `wait_for_page_load()` | covered |
| Step 5: verify both tags shown after reload | Both tag chips displayed | Step 5 | both chip accessible names present post-reload | covered |
| Expected Final State: both tags present after reload | — | Step 5 | see above (case-text hyphen/underscore note above) | covered |
| Pass criterion: "all steps complete without errors" | — | Steps 1-5 | 0 console errors captured after Save + after reload | covered |
| Pass criterion: "both tags persist... after reload" | — | Step 5 | see above | covered |
| Fail criterion: "one or both tags missing after reload" | n/a (negative condition) | Step 5 | exact chip-count + per-tag presence check (not just "at least one") | covered |

### Axis 2 — observables asserted beyond the case text

| Observable | Why asserted |
|---|---|
| Save PUT returns `201 Created` (network-level) | The project's existing pattern for Save-persists cases (ELITEA-1872/1873/1881) asserts the network status as the causal mechanism, not just the DOM — catches a silent client-side-only "looks saved" false positive |
| 0 console errors after Save and after reload | Side-channel check per the skill's mandatory "silent errors are the worst bugs" rule — the Tags `AutoCompleteDropDown` component is shared with Pipelines/Skills, a regression there could silently no-op |
| Chip order preserved (`regression_test` then `automation`) after reload | Not explicitly required by the case text, but a cheap, free assertion once both chips are being read positionally — catches a hypothetical sort-order regression on the backend `tags` array |

## Concrete Handles (testid-only, per `.agents/testing.md` § Locator policy)

| Element | Handle | Status |
|---|---|---|
| Save button | `agent-save-button` | pre-existing (`AgentFormPage.save_button`) |
| Tags field wrapper | (no testid needed — reached via `tags_input`/chip locators directly) | n/a |
| Tags input (real `<input>`) | **testid needed: `agent-tags-input`** | needs-adding — thread `inputTestId="agent-tags-input"` onto `ApplicationEditForm.jsx`'s `<TagEditor>` call site's Agent branch (mirrors the existing `inputTestId={isFromPipeline ? 'pipeline-tags-input' : undefined}` ternary — flip the `else` branch from `undefined` to `'agent-tags-input'`). `TagEditor` → `AutoCompleteDropDown` already wires `inputTestId` straight onto the input's `data-testid` (confirmed via source read, `AutoCompleteDropDown.jsx:290`); no capability gap, pure threading. |
| Tag chip (rendered, one per committed tag) | **testid needed: `agent-tags-chip-{tag_name}`** (dynamic, parameterized by tag name) | needs-adding — `AutoCompleteDropDown.jsx:213-214` already supports `chipTestId` as **either a static string or a function of the option** (`typeof chipTestId === 'function' ? chipTestId(option) : chipTestId`). Use the function form: `chipTestId={option => \`agent-tags-chip-${option.name}\`}` so this case's two chips (`agent-tags-chip-regression_test`, `agent-tags-chip-automation`) are independently addressable — a single static testid (the Pipeline form's current shape) would leave both chips sharing one selector, forcing brittle `.nth()` positional indexing to tell them apart, which this case explicitly needs (verifying BOTH specific tags, not just "2 chips exist"). Page-object side: class-level template constant per `.agents/testing.md`'s dynamic-testid pattern, e.g. `AGENT_TAGS_CHIP = '[data-testid="agent-tags-chip-{}"]'`, used as `self.page.locator(self.AGENT_TAGS_CHIP.format(tag_name))`. |
| Tag chip delete icon | **testid needed: `agent-tags-chip-delete-{tag_name}`** (dynamic) — **not exercised by THIS case** (ELITEA-1878 never removes a tag); see the sibling AFS for ELITEA-1879, which DOES touch it. Per canon #511 scope discipline, do not wire this prop unless ELITEA-1879's implementation actually calls it. | needs-adding (ELITEA-1879's implementation, not this one) |

**Naming rationale:** `{section}-{element}-{param}` per `.agents/testing.md`
§ Locator policy — `agent` (call-site section, matches the pre-existing
`agent-save-button`/`agent-name-input` convention, distinguishing this from
the Pipeline form's `pipeline-tags-*` on the SAME shared `TagEditor`
component — role-overrides § "shared components never hardcode
feature-scoped testids" is satisfied because the testid is supplied at the
Agent call site via the same ternary pattern already used for
`pipeline-tags-input`/`pipeline-tags-chip`, not hardcoded inside
`TagEditor.jsx`/`AutoCompleteDropDown.jsx` themselves).

## Network Behavior

- Save: `PUT /api/v2/elitea_core/application/prompt_lib/{projectId}/{agentId}`
  → `201 Created`. Confirmed live (project id `399`, agent id `5189`).
- Reload: `GET /api/v2/elitea_core/application/prompt_lib/{projectId}/{agentId}`
  → `200 OK`, response includes the persisted `tags` on
  `version_details.tags` (per `ApplicationEditForm.jsx`'s
  `formik.values?.version_details?.tags` read/write path).
- Tags-autocomplete option list: `GET /api/v2/elitea_core/tags/prompt_lib/{projectId}?...&entity_coverage=application`
  fires on Tags-field mount (project-wide existing-tag suggestions) — not
  required for this case's assertions (both tags are freeSolo-typed new
  values, not selected from suggestions), noted for completeness.

## Known Defects Found During Exploration

None. Add/save/reload-persist for two tags works correctly — confirmed live,
no functional defect. The only gap found (missing testids on the Agent
Tags input/chips) is implementer work (`add-data-testid`), not a product
bug, per this project's "missing testid alone ⇒ add it" policy.

## Cleanup

1. Live exploration (this analyst pass) was performed against the shared
   `manual_test_agent` (id `5189`, project `399`) — added `regression_test`
   + `automation`, saved, reloaded, verified persistence
   (`test-results/screenshots/ELITEA-1878-step-05-tags-persist-after-reload.png`).
2. **Both tags removed again and re-saved** before handoff (see ELITEA-1879's
   own steps below, which reused the same agent to test tag removal) —
   `manual_test_agent` is back to zero tags, confirmed via a final reload +
   accessibility-snapshot check (Tags field shows only the empty combobox,
   no chips).
3. The automated test itself must use its own dedicated, disposable agent
   (see Preconditions/Implementation guidance above) — do not touch
   `manual_test_agent` from automated test code.
