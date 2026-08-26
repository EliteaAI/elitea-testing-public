# Test Case: Save and Discard buttons are only active when there are unsaved changes

## Metadata
- **TMS ID**: ELITEA-2275
- **Source case**: `.agents/automation/settings-w03/cases/ELITEA-2275.md`
  (snapshot; TMS module `settings-project-params`; TMS file
  `settings/project-params/ELITEA-2275_save-and-discard-buttons-are-only-active-when-there-are-unsa.md`)
- **Linked Story**: none
- **Priority**: l3 (medium) → **`@pytest.mark.p2`**
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}` = 399), 2026-08-26
- **User set**: `${TEST_USER}` (localhost `auth_state`)
- **Analyst**: test-automation-engineer (Axel), combined analyst+implementer slot
- **Status**: ready-for-automation

## Classification note — declared divergence (reverse-masking guard)

Case step 5 — *"Click Discard — verify buttons become inactive again"* — cannot be
observed **in place**: `handleDiscard` navigates away from the editor
(`onNavigate('saved')`), so a moment after the click there are no Save/Discard buttons
to read (confirmed live 2026-08-26). The case's observable is *the dirty state was
cleared, so the buttons are no longer active*, and that is asserted on the editor the
user next opens: it renders with both buttons **disabled**, exactly as on first entry.

Both halves of the disappearance are asserted, so nothing is lost: the buttons are gone
from the DOM immediately after Discard (count 0 — the product left the editor), and they
are back and **disabled** when the editor is re-entered. Module-wide case-text drift
already filed as **#1792**; no new ticket.

## Preconditions
- User is logged in (localhost dev-token auth).
- Non-Public project (`${ELITEA_PROJECT_ID}` = 399 "Private").
- **Existing saved content** — the case's step 1 says so explicitly ("with existing
  saved content"), and it is what makes the sibling button `Discard` rather than
  `Cancel`. Established by the pre-existing `project_context_seed` fixture.

## Test Data
### reuse-existing
- `${ELITEA_PROJECT_ID}` = `399`.
- Fixture `project_context_seed`.

### generate-per-test
- Seed body: `## ELITEA-2275 saved content`.
- The change of case step 3: a single typed character (`X`) — the minimum that makes
  `isDirty` true, which is precisely what the case is about.

## Fidelity Declaration

| What is substituted | Transit or terminal | Authority / real observable |
|---|---|---|
| Precondition seeding of the Project Context **`content`** via `PUT` | **Transit** | It only satisfies the case's own "with existing saved content" precondition so the editor opens in edit mode. Every asserted value — each button's `disabled` state at each phase, the label, the post-Discard navigation, the reverted content — is produced by the product. The seed's *text* is never asserted: the baseline the post-Discard content is compared against is **read off the editor at step 2** (the ELITEA-2274 pattern), never the seed constant. |
| The **`enabled` flag** on that `PUT` | **Not substituted** | Seeded with `content` only; `enabled` defaults to `None` = echo the product's own value. This case never asserts the flag. |

No `route.fulfill`, no injected state. This case types a real keystroke; it does not
need the clipboard path at all.

## Test Steps

1. **Setup** — `project_context_seed("## ELITEA-2275 saved content")` (content only).
2. Navigate to `${BASE_URL}/settings/project-context` with that saved content, then
   click **Edit** — case step 1.
   - **Verify**: URL is `${BASE_URL}/settings/project-context/edit`, the editor is
     visible and shows non-empty content (the "existing saved content" precondition is
     really in force, not an empty create-mode editor).
   - **Verify**: the sibling button's label is exactly `Discard` (edit mode). In create
     mode the same button reads `Cancel` and calls a different handler.
   - **Read the baseline off the product here** — `get_editor_lines()`, not the seed
     constant. Guard it twice so step 6's comparison cannot go vacuous: the baseline is
     non-empty, and it does not already contain the character step 4 will type.
3. **Buttons are inactive when nothing has changed** — case step 2.
   - **Verify**: `project-context-save-button` is **disabled**.
   - **Verify**: `project-context-discard-button` is **disabled**.
4. **Make a change** — case step 3: click into the editor and type one character.
   - **Verify**: the editor's content now ends with that character (the change really
     landed; otherwise step 4 would assert nothing).
5. **Buttons become active** — case step 4.
   - **Verify**: Save is **enabled**.
   - **Verify**: Discard is **enabled**.
6. **Click Discard; buttons become inactive again** — case step 5, the Expected Final
   State.
   - Click `project-context-discard-button`.
   - **Verify**: the app navigates to `${BASE_URL}/settings/project-context` and the
     saved view renders — and both buttons have **count 0** (the editor, and with it the
     buttons, is gone; this is *how* the product deactivates them).
   - Re-open the editor (**Edit**).
   - **Verify**: Save is **disabled** and Discard is **disabled** — the dirty state was
     cleared by the Discard, so the editor the user next sees offers neither action.
   - **Verify**: the typed character is absent from the editor's content — the buttons
     are inactive *because there is nothing unsaved*, not because the change silently
     stuck.
   - **Verify**: the content matches the **step-2 baseline** exactly (the lines read off
     the product before the edit) — the revert restored what was there, it did not merely
     drop the character.
7. **Teardown** — fixture deletes the Project Context (tolerates 404).

## Concrete Handles

| Element | Handle (testid) | Provenance | Verified |
|---|---|---|---|
| Saved-view toggle card (readiness) | `project-context-toggle-card` | on `automation/testids` only (EliteaAI/EliteaUI@b05bbc9a) | live 2026-08-26 |
| Saved-view Edit button | `project-context-edit-button` | on `automation/testids` only (EliteaAI/EliteaUI@b05bbc9a) | live 2026-08-26 |
| Editor content | `project-context-editor-content` | **on-main ✓** | live 2026-08-26 |
| Save button | `project-context-save-button` | **on-main ✓** | live 2026-08-26 |
| Discard button | `project-context-discard-button` | on `automation/testids` only (EliteaAI/EliteaUI@b05bbc9a) | live 2026-08-26 |

## Coverage Map

### Axis 1 — every case element

| # | Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| 1 | Navigate to Settings → Project Context with existing saved content | page loads | Step 2 | saved view → Edit → editor route, non-empty content, label `Discard` | covered |
| 2 | Save and Discard inactive when no changes made | holds | Step 3 | `to_be_disabled()` on both | asserted |
| 3 | Make a change in the editor | completes | Step 4 | editor content ends with the typed character | asserted |
| 4 | Save and Discard become active | holds | Step 5 | `to_be_enabled()` on both | asserted |
| 5 | Click Discard — buttons become inactive again | holds (final state) | Step 6 | both count 0 right after the click (product left the editor) **and** both disabled on the re-opened editor, whose content is back to the step-2 baseline with the typed character gone | asserted (location divergence declared) |
| P | Precondition: user logged in | — | Setup | `auth_state` | covered |
| P | Precondition: existing saved content | — | Setup | `project_context_seed` (transit, declared) | covered |

### Axis 2 — observables asserted beyond the case

| Observable | Why |
|---|---|
| The editor shows non-empty content at step 2 | Distinguishes the case's stated precondition (existing saved content, edit mode) from an empty create-mode editor, where the same testids exist but the sibling button is `Cancel` with different behaviour. Without it the whole case could silently run the wrong flow. |
| Discard's label is exactly `Discard` | Same reason, stated as an assertion rather than an assumption. |
| The typed character is absent after Discard | Pins *why* the buttons are inactive. Buttons could also be disabled while a save is in flight (`disabled={!isDirty \|\| isSaving}`); asserting the change is gone rules that reading out. |
| Post-Discard navigation to `/settings/project-context` | The product's real mechanism for deactivating the buttons; pinning it makes the declared divergence test-enforced rather than prose. |
| No console errors across the run | Standard side-channel check on this surface. |

## Known Defects
- **#1792 (case text)** — module-wide naming and the in-place assumption of step 5.
  Pre-existing, not re-filed.

## Blocked Steps
None — every step above was executed live and observed 2026-08-26.
