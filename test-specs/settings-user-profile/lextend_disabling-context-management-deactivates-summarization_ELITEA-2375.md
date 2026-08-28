# Test Case: Disabling context management also deactivates summarization regardless of summarization toggle state

## Metadata
- **TMS ID**: ELITEA-2375
- **Priority**: l3 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot), batch `settings-w08`, 2026-08-28
- **Status**: extend-existing
- **Surface digest**: `test-specs/settings-user-profile/_surface.md` →
  `_surface/memory-context-management.md`

## Extension target

- **Covering spec**: `automation/tests/ui/settings/test_context_management_toggle.py`
  (`class TestContextManagementToggle`) — merged on `origin/automation/base`.
- **Covering AFS**: `test-specs/settings-user-profile/l3_context-management-toggle-enables-disables-fields_ELITEA-2374.md`
- **Behavioural overlap**: the covering method
  `test_context_management_toggle_enables_disables_fields` (ELITEA-2374)
  already drives the same `/settings/memory` page and the same
  `UserProfileSettingsPage`, and already asserts that turning Context
  Management OFF unmounts Max Context Tokens, Preserve Recent Messages and
  the Automatic Summarization **toggle**, and that turning it back ON
  remounts them with prior values.
- **The gap this case adds** (why it is not `already-covered`):
  1. the covering method never establishes "**both** toggles ON" as an
     explicit precondition — this case's premise is *"regardless of
     summarization toggle state"*, so Automatic Summarization being ON before
     the parent is switched off is load-bearing, not incidental;
  2. the covering method asserts only the Automatic Summarization *toggle*
     disappears — it never asserts the sub-section's own two **fields**
     (`summarization-instructions-textarea`, `target-summary-tokens-input`)
     are gone, which is this case's steps 4–5;
  3. the covering method never asserts that on re-enable the **summarization
     state itself survives** (toggle reads ON again, its two fields are
     enabled) — this case's step 7 ("summarization settings become active
     again").
- **Extension mechanic**: additive — a new
  `test_disabling_context_management_deactivates_summarization` method
  appended to the existing `TestContextManagementToggle` class, reusing the
  module-level `_is_autosave_put_response` / `_is_autosave_get_response`
  helpers. Every existing method stays byte-identical.

## Preconditions
- User is logged in (`auth_state` fixture; localhost bypass).
- Per-user profile setting — no project-level precondition.

## Test Data
### reuse-existing
- No fixed test data. Both toggles are ON on the shared `${TEST_USER}`
  account today, and both are established as preconditions by the test
  itself (turn ON if OFF). Field VALUES are never hard-asserted against
  literals — per the surface digest's *Test data gotcha*, this shared
  account carries whatever earlier sessions saved (observed this session:
  Max Context Tokens `6400`→`32000`, Preserve Recent Messages `5`→`10`,
  Target Summary Tokens `4096`→`300`). Capture-and-compare only.

## Test Steps
1. Navigate to `${BASE_URL}/settings/memory` (Settings → Memory).
   - **Verify**: `context-management-section` is visible.
2. Ensure **both** toggles are ON (this case's step 2, "Enable both context
   management and summarization toggles"):
   - if `context-management-toggle` is OFF, click it and wait for the
     autosave round-trip (`PUT /api/v2/social/author/` → 200 + the GET
     refetch);
   - then, if `automatic-summarization-toggle` is OFF, click it and wait for
     the same round-trip.
   - **Verify**: both toggles read ON.
3. Read and store the current Target Summary Tokens value
   (`original_target_tokens`) for the step-7 round-trip check. Assert it is a
   positive integer (never a literal).
4. Click `context-management-toggle` OFF; wait for the autosave PUT → 200 and
   the GET refetch.
   - **Verify**: the toggle reads OFF.
5. **Verify**: the Automatic Summarization toggle
   (`automatic-summarization-toggle`) is **absent from the DOM**
   (`to_have_count(0)`) — the case's "grayed out / inactive" wording
   describes a *conditional unmount* live (see § Coverage Map,
   clarification #1238).
6. **Verify**: the summarization **fields** —
   `summarization-instructions-textarea` and `target-summary-tokens-input` —
   are likewise **absent from the DOM** (`to_have_count(0)`), i.e. uneditable
   because they no longer exist, not because a `disabled` prop is set. (This
   is the sub-section's outer mechanism; contrast ELITEA-2377, where the
   Automatic Summarization toggle's OWN disable of the same two fields IS a
   real `disabled` prop.)
7. Click `context-management-toggle` back ON; wait for the autosave PUT → 200
   and the GET refetch.
   - **Verify**: `automatic-summarization-toggle` is visible again **and
     still reads ON** — the summarization state survived the parent's
     off/on cycle (this is the case's "regardless of summarization toggle
     state" premise closing).
   - **Verify**: `summarization-instructions-textarea` and
     `target-summary-tokens-input` are visible and **enabled**
     (`to_be_enabled()`) — "summarization settings become active again".
   - **Verify**: Target Summary Tokens' value equals `original_target_tokens`
     from step 3 (state preserved, not reset).

## Expected Results
- With Context Management OFF, the entire Automatic Summarization
  sub-section — toggle **and** both fields — is unmounted.
- With Context Management back ON, the sub-section remounts with the
  summarization toggle still ON and both fields enabled and carrying their
  prior values.
- Every toggle click autosaves via `PUT /api/v2/social/author/` → 200.

## Coverage Map

### Axis 1 — Case coverage

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Personalization | Page/section loads | AFS step 1 | step 1: `context-management-section` visible | clarification *(route is Settings → Memory; `/settings/personalization` 404s — already tracked by EliteaAI/elitea-testing-public#1238, no new ticket)* |
| 2 Enable both context management and summarization toggles | Both ON, no error | AFS step 2 | step 2: both toggles read ON (+ autosave PUT 200 for each click actually made) | asserted |
| 3 Turn context management toggle OFF | Toggle responds | AFS step 4 | step 4: toggle unchecked + autosave PUT 200 | asserted |
| 4 Verify the summarization toggle appears grayed out / inactive | Toggle inactive | AFS step 5 | step 5: `automatic-summarization-toggle` `to_have_count(0)` | asserted *(mechanism is conditional UNMOUNT, not a grayed-out `disabled` render — asserted as absence, which is the live contract; case-text wording drift, same root cause as #1238)* |
| 5 Verify the summarization fields (Summarization Instructions, Target Summary Tokens) are uneditable | Fields uneditable | AFS step 6 | step 6: both fields `to_have_count(0)` | asserted *(same unmount mechanism — "uneditable" holds a fortiori: the fields are not in the DOM)* |
| 6 Turn context management back ON | Toggle responds | AFS step 7 | step 7: autosave PUT 200 + toggle ON | asserted |
| 7 Verify summarization settings become active again | Summarization active | AFS step 7 | step 7: summarization toggle visible AND still checked; both fields visible + `to_be_enabled()`; Target Summary Tokens value round-trips | asserted |

### Axis 2 — Analyst additions
- Step 3/7 value round-trip on Target Summary Tokens — *added: proves
  "active again" means the prior configuration returned, not a reset to
  defaults.*
- Step 7's "toggle still reads ON" — *added: this is what makes the case's
  "regardless of summarization toggle state" premise falsifiable; without it
  the re-enable assertion would pass even if the product silently reset
  summarization to OFF.*
- Autosave PUT→200 assertions on each toggle click — *added: confirmed live
  as the reliable wait signal (the page has no Save button); reuses the
  covering spec's existing helpers.*

## Cleanup
- None beyond the flow: steps 4→7 are a full OFF→ON round-trip that leaves
  Context Management ON and Automatic Summarization ON, exactly as found.
  The implementation additionally carries the covering spec's existing
  `finally` safety net (restore Context Management ON if a mid-flow
  assertion fails).

## Concrete Handles (discovered during exploration)

| Element | Testid | PROVENANCE (verified 2026-08-28, fresh `git fetch origin`) | Notes |
|---|---|---|---|
| Context Management section | `context-management-section` | on-main ✓ | Pre-existing on the page object. |
| Context Management toggle | `context-management-toggle` | on-main ✓ | Pre-existing. |
| Automatic Summarization toggle | `automatic-summarization-toggle` | on-main ✓ | **Promoted since the ELITEA-2377 session** (digest previously said `automation/testids` only). |
| Summarization Instructions textarea | `summarization-instructions-textarea` | on-main ✓ | **Promoted since the ELITEA-2377 session.** |
| Target Summary Tokens input | `target-summary-tokens-input` | on-main ✓ | **Promoted since the ELITEA-2377 session.** |
| Max Context Tokens / Preserve Recent Messages inputs | `max-context-tokens-input`, `preserve-recent-messages-input` | on-main ✓ | Not asserted by this case; listed because the same unmount removes them. |

No new testid work — every handle this case needs already exists and is now
on `main`.

## Network Behavior
- `PUT /api/v2/social/author/` → 200 on every toggle click, immediately
  followed by `GET /api/v2/social/author/` (refetch). Both are waited on via
  the covering spec's `_is_autosave_put_response` / `_is_autosave_get_response`
  helpers — the GET wait prevents the documented race where a second click
  lands before the first click's refetch resolves.

## Known Defects Found During Exploration
- None new. Route drift is the existing clarification
  **EliteaAI/elitea-testing-public#1238**.
- **EliteaAI/elitea-testing-public#1129** (numeric fields never autosave when
  typed) did **not** reproduce this session — Max Context Tokens, Preserve
  Recent Messages, Summarization Instructions and Target Summary Tokens all
  autosaved and survived a reload (see the ELITEA-2376/2379 family AFS).
  Not exercised by this case, recorded for the digest.

## Blocked Steps
- None. Every case step was executed live and observed.

## Automation Hints
- Framework: Playwright + pytest.
- Page object: `automation/pages/user_profile_settings_page.py` — every
  locator and helper this case needs already exists
  (`is_/enable_/disable_context_management`,
  `is_/enable_/disable_automatic_summarization`,
  `get_target_summary_tokens`). **No page-object change required.**
- Test file: append ONE method to `TestContextManagementToggle` in
  `automation/tests/ui/settings/test_context_management_toggle.py`; no new
  file, no new class. Verify additivity:
  `git diff <base>...HEAD -- automation/tests/ui/settings/test_context_management_toggle.py | grep -E '^-[^-]'` → empty.
