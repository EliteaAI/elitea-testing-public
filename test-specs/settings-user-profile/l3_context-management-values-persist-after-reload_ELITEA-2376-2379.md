# Test Case (FAMILY): Context Management / Summarization values persist after autosave and reload

## Metadata
- **TMS IDs**: ELITEA-2376, ELITEA-2379 — **family AFS** (one flow, two
  field-set variants; one parameterized spec, one row per case)
- **Priority**: l3 (both cases' priority `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids`, DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: test-automation-engineer (combined analyst+implementer slot), batch `settings-w08`, 2026-08-28
- **Status**: ready-for-automation
- **Surface digest**: `test-specs/settings-user-profile/_surface.md` →
  `_surface/memory-context-management.md`

## Why one family AFS

Both cases are the identical flow — *set field(s) on `/settings/memory` →
blur to trigger the page's autosave → reload the page → the typed values are
still there* — differing only in **which fields** are written and **which
sub-section's precondition** must hold. They are flow-variants, not distinct
behaviours, so they become ONE parameterized spec with a row per TMS case,
each row asserting its **own** expected values.

| Row (TMS ID) | Sub-section | Fields set → expected after reload | Extra precondition |
|---|---|---|---|
| ELITEA-2376 | DEFAULT CONTEXT MANAGEMENT | `max-context-tokens-input` = `32000`, `preserve-recent-messages-input` = `10` | Context Management ON |
| ELITEA-2379 | DEFAULT SUMMARIZATION | `summarization-instructions-textarea` = `"Summarize briefly, focus on key actions."`, `target-summary-tokens-input` = `300` | Context Management ON **and** Automatic Summarization ON |

## Preconditions
- User is logged in (`auth_state`; localhost bypass).
- Context Management toggle ON (both rows) — the numeric fields are
  conditionally unmounted while it is OFF.
- Automatic Summarization toggle ON (ELITEA-2379 row only) — its two fields
  carry a real `disabled` prop while it is OFF.

## Test Data
### create-per-run (typed into the shared account, restored afterwards)
- ELITEA-2376: `32000` / `10` — both inside the client-side schema limits
  (`max_context_tokens` ∈ [1000, 10 000 000]; Preserve Recent Messages has no
  upper bound issue at 10).
- ELITEA-2379: `"Summarize briefly, focus on key actions."` / `300` — `300`
  is inside `VALIDATION_LIMITS.MAX_TOKENS` = [100, 4096], so the autosave is
  not blocked by validation.
- These are per-user profile values on the shared `${TEST_USER}` account.
  **Read-before-write and restore in teardown** (surface digest § Test data
  gotcha): never assume a default, never leave the account on the test's
  values.

## Test Steps
*(one pass per row; `FIELDS` = that row's field/value pairs)*

1. Navigate to `${BASE_URL}/settings/memory`.
   - **Verify**: `context-management-section` is visible.
2. Ensure the row's preconditions hold (Context Management ON; for the
   ELITEA-2379 row also Automatic Summarization ON), clicking the toggle and
   waiting for the autosave round-trip only when it is currently OFF.
3. Read the current value of every field in `FIELDS` and store it
   (`original_values`) for teardown restoration.
4. For each `(field, value)` in `FIELDS`: type `value` into the field
   (clear + `type()` per keystroke — MUI/React `onChange` does not fire on
   `fill()` alone) and blur it, which is the page's autosave trigger
   (`useFormikAutoSaveOnBlur`). Wait for `PUT /api/v2/social/author/` → 200
   for **each** field write, and assert the status.
   - *(This is the cases' "Click somewhere on ui to trigger autosave" /
     "Click outside to trigger autosave" step — there is no Save button on
     this page.)*
5. Reload the page (`${BASE_URL}/settings/memory`) and wait for the section
   to render.
6. **Verify**: every field in `FIELDS` reads back its written value exactly
   — ELITEA-2376: Max Context Tokens `32000` **and** Preserve Recent Messages
   `10`; ELITEA-2379: Summarization Instructions
   `"Summarize briefly, focus on key actions."` **and** Target Summary Tokens
   `300`.

## Expected Results
- Each typed value fires an autosave `PUT /api/v2/social/author/` → 200 on
  blur (confirmed live: four PUTs for four field writes across the two rows).
- After a full page reload the persisted values are rendered back verbatim.

## Coverage Map

### Axis 1 — Case coverage

#### ELITEA-2376

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Personalization → DEFAULT CONTEXT MANAGEMENT | Section loads | AFS step 1 | step 1: `context-management-section` visible | clarification *(live route is Settings → Memory; `/settings/personalization` 404s — tracked by EliteaAI/elitea-testing-public#1238)* |
| 2 Set Max Context Tokens to 32000 | Accepted, no error | AFS step 4 | step 4: field typed; autosave PUT → 200 | asserted |
| 3 Set Preserve Recent Messages to 10 | Accepted, no error | AFS step 4 | step 4: field typed; autosave PUT → 200 | asserted |
| 4 Click somewhere on UI to trigger autosave | Control responds | AFS step 4 (blur) | step 4: blur → `PUT /api/v2/social/author/` → 200 asserted per field | asserted |
| 5 Reload the page | Reload completes | AFS step 5 | step 5: navigation + section visible again | asserted |
| 6 Verify Max Context Tokens shows 32000 and Preserve Recent Messages shows 10 | Both values persisted | AFS step 6 | step 6: `get_max_context_tokens() == 32000` and `get_preserve_recent_messages() == 10` | asserted |

#### ELITEA-2379

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Navigate to Personalization → DEFAULT SUMMARIZATION | Section loads | AFS step 1 | step 1: `context-management-section` visible | clarification *(same route drift, #1238; "DEFAULT SUMMARIZATION" is the Automatic Summarization sub-section of Settings → Memory)* |
| 2 Enable automatic summarization | Toggle ON | AFS step 2 | step 2: `automatic-summarization-toggle` ON (click + autosave PUT 200 only when it starts OFF) | asserted |
| 3 Enter summarization instructions "Summarize briefly, focus on key actions." | Field shows the value | AFS step 4 | step 4: typed value present in the field before blur; autosave PUT → 200 | asserted |
| 4 Set Target Summary Tokens to 300 | Accepted | AFS step 4 | step 4: field typed; autosave PUT → 200 | asserted |
| 5 Click outside to trigger autosave | Control responds | AFS step 4 (blur) | step 4: blur → PUT → 200 asserted per field | asserted |
| 6 Reload the page | Reload completes | AFS step 5 | step 5 | asserted |
| 7 Verify Summarization Instructions shows "Summarize briefly, focus on key actions." | Value persisted | AFS step 6 | step 6: exact string equality | asserted |
| 8 Verify Target Summary Tokens shows 300 | Value persisted | AFS step 6 | step 6: `get_target_summary_tokens() == 300` | asserted |

### Axis 2 — Analyst additions
- The per-field autosave `PUT → 200` assertion (step 4) — *added: the cases
  say "trigger autosave" but assert nothing about it; asserting the PUT makes
  the reload check a genuine persistence check rather than a React-state
  read, and it is the correct wait signal (no Save button exists).*
- Read-before-write + teardown restore — *added: these are per-user account
  values on a SHARED test account; leaving `32000/10/300` behind would poison
  sibling settings and chat tests (surface digest § Test data gotcha).*

## Cleanup
- Restore every field written by the row to the value read in step 3, and
  restore any toggle the test itself flipped. Verified restorable through the
  same blur-autosave path.

## Concrete Handles (discovered during exploration)

| Element | Testid | PROVENANCE (verified 2026-08-28, fresh `git fetch origin`) | Notes |
|---|---|---|---|
| Context Management section | `context-management-section` | on-main ✓ | |
| Context Management toggle | `context-management-toggle` | on-main ✓ | Precondition handle. |
| Max Context Tokens input | `max-context-tokens-input` | on-main ✓ | ELITEA-2376 row. |
| Preserve Recent Messages input | `preserve-recent-messages-input` | on-main ✓ | ELITEA-2376 row. **Promoted to `main` since the ELITEA-2374 session** (digest said testids-only). |
| Automatic Summarization toggle | `automatic-summarization-toggle` | on-main ✓ | ELITEA-2379 precondition. |
| Summarization Instructions textarea | `summarization-instructions-textarea` | on-main ✓ | ELITEA-2379 row. |
| Target Summary Tokens input | `target-summary-tokens-input` | on-main ✓ | ELITEA-2379 row. |

No new testid work.

## Network Behavior
- `PUT /api/v2/social/author/` → 200 on every field blur that passes
  client-side validation, followed by a `GET /api/v2/social/author/` refetch.
  Live capture this session showed 4 PUT/GET pairs for the four field writes.
- A value that fails client-side validation fires **no** PUT
  (`useFormikAutoSaveOnBlur` runs `validateForm()` first) — all values used
  here are in range, so a missing PUT is a real failure, not an expected one.

## Known Defects Found During Exploration
- **EliteaAI/elitea-testing-public#1129 did NOT reproduce** (OPEN issue:
  "the three numeric fields on `/settings/memory` never autosave when typed;
  values revert on reload"). This session, all four fields — Max Context
  Tokens, Preserve Recent Messages, Summarization Instructions, Target
  Summary Tokens — autosaved (PUT → 200) and survived a full reload. This
  extends the earlier partial contradictions recorded in the digest
  (ELITEA-2378 for Target Summary Tokens, ELITEA-2391 for Max Context
  Tokens) to **Preserve Recent Messages**, the last untested field. **The
  issue looks fixed; a comment with this evidence is warranted rather than a
  new ticket** (agents never close issues).
- No other defect found; every step behaved as the case text describes.

## Blocked Steps
- None.

## Automation Hints
- Framework: Playwright + pytest. New spec file
  `automation/tests/ui/settings/test_context_management_values_persist.py`
  (new flow, new class — NOT an extension of
  `test_context_management_toggle.py`, whose class covers toggle
  mount/disable mechanics, not persistence).
- ONE `@pytest.mark.parametrize` over the two rows above, each row tagged
  with its TMS id, each asserting its own expected values.
- Page object `automation/pages/user_profile_settings_page.py` needs three
  small ADDITIVE helpers (the existing setters cover only Max Context Tokens
  and Target Summary Tokens):
  `set_preserve_recent_messages(value)`, `set_summarization_instructions(text)`,
  `get_summarization_instructions()`. Model them on the existing
  `set_target_summary_tokens()` — clear + per-keystroke `type()` + `Tab`,
  and **no** built-in autosave wait, so the caller can wrap the call in
  `page.expect_response(...)` and assert the PUT status. Do not modify
  `set_max_context_tokens()` (4+ existing callers).
