# Test Case: Context management toggle enables and disables token fields

## Metadata
- **TMS ID**: ELITEA-2374
- **Linked Story**: EliteaAI/elitea-testing-public#882
- **Priority**: l3
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), batch `elitea-2374-context-mgmt-toggle`
- **Status**: ready-for-automation

## Preconditions
- User is logged in to the Elitea platform (`auth_state` fixture).
- No project-level precondition — this is a per-user profile setting.

## Test Data
### reuse-existing
- No fixed test data required. **Do not hard-assert a specific numeric
  default** for Max Context Tokens / Preserve Recent Messages — see Coverage
  Map row for case step 4 and § Blocked Steps. The shared test account
  (`${TEST_USER}`) already carries persisted values (observed: `10000` /
  `5`) from earlier manual/automated sessions; capture-and-compare against
  the value read at test start instead of a literal `64000`.

## Test Steps
1. Navigate to `${BASE_URL}/settings/memory` (Settings → Memory tab).
   - **Verify**: the "Context Management" accordion section
     (`context-management-section`) is visible and expanded by default.
2. Verify the "Context Management" toggle (`context-management-toggle`) is
   present. If it is currently OFF, turn it ON first (precondition for the
   rest of the flow) and wait for the autosave round-trip
   (`PUT /api/v2/social/author/` → 200).
3. With the toggle ON, verify Max Context Tokens
   (`max-context-tokens-input`) and Preserve Recent Messages
   (`preserve-recent-messages-input`) inputs are **visible and enabled**
   (not `disabled`, editable via click+type).
4. Read the current values of both fields and assert they are non-empty
   positive integers. **Do not assert literal `64000` / `5`** — see Test
   Data note above. Store the read values as `original_max_tokens` /
   `original_preserve_messages` for the restore-verification in step 8.
5. Click the Context Management toggle (`context-management-toggle`) to
   turn it OFF. Wait for the autosave round-trip
   (`PUT /api/v2/social/author/` → 200; UI also shows a "Settings saved
   successfully" toast).
6. Verify Max Context Tokens (`max-context-tokens-input`) and Preserve
   Recent Messages (`preserve-recent-messages-input`) inputs are **absent
   from the DOM** (`to_have_count(0)` / `not_to_be_visible()`) — the
   product unmounts them entirely rather than rendering them
   disabled/grayed-out. (Case text says "grayed out and uneditable";
   live mechanism is conditional unmount — clarification filed
   EliteaAI/elitea-testing-public#1238. Absence is still a correct,
   arguably stronger, assertion of "uneditable".)
7. Verify the "Automatic Summarization" sub-section is inactive: the
   Automatic Summarization toggle (`automatic-summarization-toggle`) is
   **absent from the DOM**, along with its instructions/target-tokens
   fields (they unmount as one unit with the parent `MemorySummarization`
   component — same #1238 clarification).
8. Click the Context Management toggle (`context-management-toggle`) back
   ON. Wait for the autosave round-trip.
   - **Verify**: Max Context Tokens and Preserve Recent Messages inputs
     reappear, are editable, and their values equal
     `original_max_tokens` / `original_preserve_messages` from step 4
     (state is preserved across the hide/show cycle, not reset).
   - **Verify**: the Automatic Summarization toggle reappears and is
     checked (or restored to whatever state it had before step 5 — read
     it in step 4/prep if asserting exact state matters; at minimum
     assert it is present and interactive again).

## Expected Results
- Toggling Context Management OFF removes (does not merely disable) the
  Max Context Tokens field, Preserve Recent Messages field, Context Editing
  toggle, and the entire Automatic Summarization sub-section from the DOM.
- Toggling back ON restores all of the above with their prior values intact.
- Each toggle click triggers `PUT /api/v2/social/author/` → 200 (autosave;
  no explicit Save button on this page).
- No console errors during the flow (one unrelated pre-existing MUI
  `disableUnderline` prop warning was observed on `/settings/ai-personality`
  during navigation exploration — not on this page, not related to this
  case; not filed).

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Personalization → DEFAULT CONTEXT MANAGEMENT | Target page/section loads | AFS step 1 | step 1: `context-management-section` visible | clarification *(route is Settings → Memory → "Context Management", not Personalization → "DEFAULT CONTEXT MANAGEMENT"; `/settings/personalization` 404s — EliteaAI/elitea-testing-public#1238)* |
| 2 Verify toggle is present | Toggle visible | AFS step 2 | step 2: `context-management-toggle` visible | asserted |
| 3 When ON: Max Context Tokens / Preserve Recent Messages fields editable | Fields editable | AFS step 3 | step 3: both inputs visible + enabled | asserted |
| 4 Verify default values: Max Context Tokens = 64000, Preserve Recent Messages = 5 | Specific defaults shown | AFS step 4 (partial) | step 4: fields are non-empty positive integers | blocked *(exact literal defaults unverifiable on the shared `${TEST_USER}` account, which already carries persisted values from earlier sessions — see § Blocked Steps)* |
| 5 Click toggle OFF | Toggle responds | AFS step 5 | step 5: toggle unchecked + autosave PUT 200 | asserted |
| 6 Fields become grayed out and uneditable | Fields disabled | AFS step 6 | step 6: fields absent from DOM | clarification *(mechanism is unmount, not disabled/grayed — EliteaAI/elitea-testing-public#1238; functionally still "uneditable")* |
| 7 DEFAULT SUMMARIZATION sub-section becomes inactive (toggle grayed out or disabled) | Sub-section inactive | AFS step 7 | step 7: `automatic-summarization-toggle` absent from DOM | clarification *(same unmount mechanism; sub-section title is "Automatic Summarization", not "DEFAULT SUMMARIZATION" — EliteaAI/elitea-testing-public#1238)* |
| 8 Click toggle back ON — fields + summarization editable again | Fields restored, editable | AFS step 8 | step 8: fields + summarization toggle reappear with prior values | asserted |

### Axis 2 — Analyst additions
- AFS step 5/8 asserts the `PUT /api/v2/social/author/` → 200 autosave
  round-trip explicitly — *added: confirmed via network capture that toggle
  clicks autosave immediately (unlike the numeric-field free-typing path,
  which has an OPEN, unrelated bug — EliteaAI/elitea-testing-public#1129 —
  not exercised by this case since it only clicks the toggle, never types
  into the numeric fields).*
- AFS step 8 asserts state is **preserved**, not reset, across the
  hide/show cycle — *added: this is the natural counterpart to step 6's
  unmount finding; worth guarding so a future regression that resets
  values on remount is caught.*

## Cleanup
- None required. The flow ends with the Context Management toggle back ON
  and all field values equal to their pre-test state (steps 5→8 is a full
  round-trip; no persistent mutation beyond what already existed).

## Concrete Handles (discovered during exploration)

| Element | Testid | PROVENANCE | Notes |
|---|---|---|---|
| Context Management section container | `context-management-section` | on-main ✓ | `BasicAccordion` wrapper, `MemoryContextManagement.jsx` |
| Context Management toggle | `context-management-toggle` | on-main ✓ | `MemoryContextManagement.jsx:71` |
| Max Context Tokens input | `max-context-tokens-input` | on-main ✓ | `MemoryContextManagement.jsx:96` (via `inputProps['data-testid']`) |
| Preserve Recent Messages input | `preserve-recent-messages-input` | on-automation/testids only (awaiting human promotion to main) | **NEW** — added this session, `EliteaAI/EliteaUI@b8155bda`. Page object `user_profile_settings_page.py::preserve_recent_messages_input` already declared this exact testid name but could previously only reach the element via its legacy `fallback=`; the fallback should now be dropped. |
| Context Editing toggle | `context-editing-toggle` | on-main ✓ | Present in the same conditional block; NOT referenced by this case's steps — out of scope, do not touch. |
| Automatic Summarization toggle | `automatic-summarization-toggle` | on-automation/testids only (awaiting human promotion to main) | **NEW** — added this session, `EliteaAI/EliteaUI@b8155bda`, `MemorySummarization.jsx`. |

State assertion (per `.agents/testing.md` § Locator policy — state via
`data-*`, not testid-value-switching): N/A here — this case's "disabled"
state is expressed as element **absence**, not a `data-*` attribute filter,
because the product's own implementation is a conditional unmount
(`{isEnabled && (...)}` in `MemoryContextManagement.jsx`), not a `disabled`
prop toggle on a persistently-rendered element. Absence assertions
(`to_have_count(0)` / `not_to_be_visible()`) are the correct compliant
shape per canon ruling #511 (absence assertions count as references).

## Network Behavior
- `PUT /api/v2/social/author/` — fires immediately on every toggle click
  (Context Management toggle in both directions); 200 on success. This is
  the autosave mechanism for this page (no explicit Save button).
- `GET /api/v2/social/author/` — refetches after the PUT; page object's
  existing `wait_for_autosave()` (networkidle-based, with a 1s fallback
  for the persistent `/settings/memory` WebSocket) is sufficient to wait
  for this and needs no change.

## Known Defects Found During Exploration
- None found that block this case. One OPEN, unrelated bug was
  cross-referenced during exploration:
  **[EliteaAI/elitea-testing-public#1129]** (`bug`, pre-existing, filed
  under ELITEA-2218) — the numeric fields (Max Context Tokens, Preserve
  Recent Messages, Target Summary Tokens) do not autosave when **typed
  into** directly. This case never types into those fields (it only reads
  their value and clicks the parent toggle, which DOES autosave
  correctly per the same issue's own repro), so #1129 does not block or
  need a soft-assert here. Flagging for awareness only.
- Filed this session: **[EliteaAI/elitea-testing-public#1238]**
  (`question`/clarification) — case text navigation path and
  disable-mechanism description don't match the live product (see Axis 1
  rows above for the exact mapping). Not a product defect.

## Blocked Steps
- Case step 4's literal default values (`64000` / `5`) could not be
  verified against a pristine account — the shared `${TEST_USER}` account
  already has `10000` / `5` persisted from earlier sessions (test data
  pollution, not a product issue; `Preserve Recent Messages` happens to
  still read `5`, `Max Context Tokens` does not read `64000`). Automating
  a hard-coded `64000` assertion would be flaky/false-failing against this
  shared account's real state. AFS step 4 instead asserts "both fields
  are non-empty positive integers" and captures the values for the
  round-trip check in step 8. If the team wants the literal default
  verified, it needs either a fresh/reset test user or a backend/API
  reset-to-default step before this test runs — flagging for the lead to
  decide; not filed as a ticket (this is a test-design/test-data
  consideration, not a case-text-vs-product disagreement).

## Automation Hints
- Framework: Playwright + pytest (`.agents/testing.md`).
- Page object: `automation/pages/user_profile_settings_page.py` — **extend,
  don't duplicate**. Needed changes for the implementer:
  1. `navigate_to_profile()`'s docstring/route is stale: it navigates to
     `/settings/personalization`, which 404s. The correct route is
     `/settings/memory` (confirmed via live exploration and independently
     corroborated by EliteaAI/elitea-testing-public#1129's body). Update
     the navigation call and rename/re-doc the method if appropriate
     (`navigate_to_profile()` → still fine as a name, just fix the path).
  2. `max_context_tokens_input` and `preserve_recent_messages_input` both
     carry legacy `fallback=` params (forbidden in new code,
     `.agents/testing.md` § Locator policy). `max-context-tokens-input`
     is already on `main` — drop its `fallback=` outright.
     `preserve-recent-messages-input` is new this session (only on
     `automation/testids` so far) — drop its `fallback=` too; the real
     testid now exists and HMR-serves it on localhost, which is what this
     test runs against.
  3. New page-object surface needed: a way to assert the Max Context
     Tokens / Preserve Recent Messages inputs, the Context Editing toggle,
     and the Automatic Summarization toggle are **absent** when Context
     Management is OFF (e.g. `is_context_fields_visible() -> bool` using
     `.count() > 0`, or expose the raw `LocatorDescriptor`s for the test to
     assert `to_have_count(0)` directly — either is fine, match the
     existing style in the file).
  4. `preserve_recent_messages_input`, `automatic-summarization-toggle`:
     no page-object field yet for the summarization toggle — add one
     (`automatic_summarization_toggle = LocatorDescriptor(testid="automatic-summarization-toggle")`).
  5. This is a **fresh test file** — no existing merged spec covers this
     observable. `automation/tests/ui/chat/test_context_management.py`
     covers a different observable (Context Budget panel propagation to
     chat) and is currently `@pytest.mark.skip`ped for an unrelated,
     already-known reason (stale route); do not conflate the two. Suggest
     `automation/tests/ui/admin/test_context_management_toggle.py` or a
     new `automation/tests/ui/settings/` dir if one exists — check
     `.agents/testing.md` § Structure / existing `tests/ui/` layout for
     the right home for `settings-user-profile` module cases (several
     sibling `[Automate][ELITEA-237x]` cards target the same module —
     EliteaAI/elitea-testing-public#883/885/886/887/891/892/893/895/898
     — a shared page object extension here benefits all of them).
