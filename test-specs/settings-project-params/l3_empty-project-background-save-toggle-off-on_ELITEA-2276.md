# Test Case: Empty Project Background can be saved with toggle OFF and ON

## Metadata
- **TMS ID**: ELITEA-2276
- **Source case**: `.agents/automation/settings-w03/cases/ELITEA-2276.md`
  (case title carries a typo — "whith")
- **Linked Story**: none
- **Priority**: l3 (medium, per case frontmatter). **pytest marker: `@pytest.mark.p2`**
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  → DEV backend, project `Private` / `${ELITEA_PROJECT_ID}` = 399), 2026-08-26
- **User set**: `${TEST_USER}` (localhost `auth_state` skips login via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer (Sage), analyst slot
- **Status**: ready-for-automation
- **Clarifications filed**: #1793 (primary — toggle reachability), #1792 (layout drift)
- **Blocking suite defect (pre-existing, not this case)**: #1794 — see § Known Defects.

## Classification note — declared improvisation (step ORDER, not observable)

**Read this before implementing.** The case's step sequence is not performable against
the live product. Every step below was executed live; here is what the product actually
does:

1. **Step 2 → 3 is blocked by the UI.** With the toggle OFF, `ProjectContextSavedView.jsx`
   renders **Edit** and **Edit with AI** as `disabled={!enabled}` — confirmed live. So the
   Project Background editor cannot be *clicked* into while the toggle is OFF.
   The `/settings/project-context/edit` **route itself is unguarded**: typing the URL
   opens a fully working editor with the toggle OFF (confirmed live — Save/Discard
   enable normally once dirty). Direct-URL navigation is the project's own established
   navigation convention (`.agents/testing.md`: page objects navigate by bare path), so
   this is a legitimate user path, not a bypass.
2. **Steps 6-9 have no control to act on.** After saving empty content the server's
   `content` is `""`, `ProjectContextContent.jsx` computes `hasContent` false, and the
   **empty state** renders — which contains **no toggle at all**. Confirmed live: after
   the OFF-phase save, `settings-content` held exactly one testid,
   `project-context-create-button`. "Turn the Project Context toggle ON" (step 6) is
   therefore unperformable *in sequence*.

**What this AFS does.** The case's observable — *empty Project Background saves without
error, in both toggle states* — is fully verifiable, and is preserved in full. Only the
**order** changes: the OFF phase and the ON phase are run as two self-contained phases,
each re-establishing its own precondition, instead of one continuous sequence. Nothing
is dropped, weakened, or swapped; both toggle states are still exercised and the
save-without-error observable is asserted in both. Declared here per
`.agents/role-overrides.md` § Declared-improvisation protocol; clarification #1793 filed
so the case text gets fixed rather than this shape becoming doctrine.

## Preconditions
- User is logged in (localhost dev-token auth).
- Non-Public project required. `${ELITEA_PROJECT_ID}` = 399 ("Private").
- Each phase starts from a Project Context **with non-empty content** — that is the only
  state in which the toggle exists.

## Test Data
### reuse-existing
- `${ELITEA_PROJECT_ID}` = `399`.

### generate-per-test
- Seed content per phase, e.g. `"ELITEA-2276 phase A seed."` / `"... phase B seed."`.
  Values are irrelevant; only non-emptiness matters.

### API used for setup/teardown only
- `PUT .../project-context` `{content, enabled}` → 200.
- `DELETE .../project-context` → 200, or **404 when unset** (tolerate).
  Reuse/extend `clean_project_context` (`automation/fixtures/data_fixtures.py:2521`).

## Fidelity Declaration

| What is substituted | Transit or terminal | Authority / real observable |
|---|---|---|
| Per-phase seeding of a non-empty Project Context via `PUT` rather than typing + saving it in the UI | **Transit** | The case's observable is *the empty save succeeding*, driven by a real click on the real Save button and read off the product's own `PUT` response, toast and resulting view. The seed only restores "a context exists" so the toggle is reachable. |

No terminal substitution. The clearing and the saving are performed through the real
editor, with real keyboard input.

## Test Steps

### Phase A — empty save with the toggle OFF (case steps 1-5)

1. **Setup A** — `DELETE` (tolerate 404), then `PUT` `{content: "<seed A>", enabled: true}`.
2. Navigate to `${BASE_URL}/settings/project-context`.
   - **Verify**: `project-context-toggle-card` (*added during implementation — EliteaAI/EliteaUI@b05bbc9a*) is visible.
3. **Turn the toggle OFF** (case step 2). Click `project-context-enable-toggle`
   (*added during implementation — EliteaAI/EliteaUI@b05bbc9a*), waiting on the real `PUT` response.
   - **Verify**: response status **200**; the toggle is **unchecked**;
     `project-context-disabled-banner` (*added during implementation — EliteaAI/EliteaUI@b05bbc9a*) is visible.
   - **Verify**: `project-context-edit-button` (*added during implementation — EliteaAI/EliteaUI@b05bbc9a*) is **disabled** —
     this is the live fact that forces the direct-URL route below, so assert it rather
     than silently working around it.
4. Navigate directly to `${BASE_URL}/settings/project-context/edit`.
   - **Verify**: `project-context-editor-content` (**pre-existing**) is visible and its
     text equals `<seed A>` — proves the editor opened on the real saved content.
   - **Verify**: `project-context-save-button` (**pre-existing**) is **disabled**
     (not dirty yet — the control condition for step 5).
5. **Clear all content** (case step 3): click the editor, `ControlOrMeta+a`, `Backspace`.
   - **Verify**: editor text is exactly `""`.
   - **Verify**: `project-context-char-counter` (**pre-existing**) reads exactly
     `2500 characters left.` (confirmed live — note the trailing space before the
     conditional limit clause; normalize whitespace when comparing).
   - **Verify**: `project-context-save-button` is now **enabled**, and
     `project-context-discard-button` (*added during implementation — EliteaAI/EliteaUI@b05bbc9a*) is enabled.
6. **Click Save** (case step 4), waiting on the real `PUT` response.
   - **Verify**: response status is **200** — the case's literal
     "settings save without error" (case step 5).
   - **Verify**: the success toast `toast-message` (**pre-existing, app-wide**) reads
     `Project Context saved`.
   - **Verify**: URL returns to `${BASE_URL}/settings/project-context` (no `/edit`).
   - **Verify**: the **empty state** now renders — `project-context-create-button`
     (**pre-existing**) is visible. This is the live consequence of an empty save and
     is exactly why case steps 6-9 cannot follow in sequence (#1793).
   - **Verify**: `project-context-enable-toggle` count is **0** (the toggle is gone).
     Absence assertion — first-class per `.agents/testing.md` § Locator policy.

### Phase B — empty save with the toggle ON (case steps 6-9, re-ordered)

7. **Setup B** — `PUT` `{content: "<seed B>", enabled: true}` (re-establishes both a
   non-empty context and the ON state, which is also the product's default).
8. Reload `${BASE_URL}/settings/project-context`.
   - **Verify**: `project-context-enable-toggle` is **checked** (case step 6's intent —
     the toggle is ON), and `project-context-disabled-banner` count is **0**.
9. Click `project-context-edit-button` (enabled now that the toggle is ON — the
   contrast with step 3 is the point).
   - **Verify**: URL is `${BASE_URL}/settings/project-context/edit`.
   - **Verify**: editor text equals `<seed B>`.
10. **Clear all content** (case step 7) — same gesture as step 5.
    - **Verify**: editor text is `""`; Save is **enabled**.
11. **Click Save** (case step 8), waiting on the real `PUT`.
    - **Verify**: response status **200** (case step 9 — "settings save without error").
    - **Verify**: toast reads `Project Context saved`.
    - **Verify**: the empty state renders (`project-context-create-button` visible).
12. **Side channel** — no console errors across the whole run, via
    `automation/utils/console_errors.py`'s `collect_console_errors(page)`.
13. **Teardown** — `DELETE` (tolerate 404).

## Concrete Handles

| Element | Handle (testid) | Provenance | Verified |
|---|---|---|---|
| Editor content (`.cm-content`) | `project-context-editor-content` | **on-main ✓** | live 2026-08-26 |
| Editor Save button | `project-context-save-button` | **on-main ✓** | live 2026-08-26 |
| Char counter | `project-context-char-counter` | **on-main ✓** | live 2026-08-26 |
| Empty-state Create button | `project-context-create-button` | **on-main ✓** | live 2026-08-26 |
| Success toast | `toast-message` | pre-existing, app-wide (reused by `NotificationCenterPage` / `ArtifactsPage` / `ProjectContextPage`) | live 2026-08-26 |
| Settings content pane | `settings-content` | on `automation/testids` only | live 2026-08-26 |
| Toggle card container | `project-context-toggle-card` | on `automation/testids` (**added during ELITEA-2266/2267/2276 implementation** — EliteaAI/EliteaUI@b05bbc9a; awaiting human promotion to main) (`EnableToggleCard.jsx` root) | — |
| Enable toggle (switch input) | `project-context-enable-toggle` | on `automation/testids` (**added during ELITEA-2266/2267/2276 implementation** — EliteaAI/EliteaUI@b05bbc9a; awaiting human promotion to main) — caller-supplied prop from `EnableToggleCard.jsx` into shared `Switch.BaseSwitch` | — |
| "turned off" banner | `project-context-disabled-banner` | on `automation/testids` (**added during ELITEA-2266/2267/2276 implementation** — EliteaAI/EliteaUI@b05bbc9a; awaiting human promotion to main) — caller-supplied prop into shared `Banner.BannerMessage` | — |
| Saved-view Edit button | `project-context-edit-button` | on `automation/testids` (**added during ELITEA-2266/2267/2276 implementation** — EliteaAI/EliteaUI@b05bbc9a; awaiting human promotion to main) (`ProjectContextSavedView.jsx`) | — |
| Editor Discard/Cancel button | `project-context-discard-button` | on `automation/testids` (**added during ELITEA-2266/2267/2276 implementation** — EliteaAI/EliteaUI@b05bbc9a; awaiting human promotion to main) (`ProjectContextEditor.jsx`) | — |

**Endpoints observed** (used for `expect_response` waits and for setup/teardown, never
as a substitute for a UI observable):
`PUT|GET|DELETE /api/v2/elitea_core/project_context/prompt_lib/{project_id}/project-context`.
`DELETE` returns **404** when nothing is set — tolerate in teardown.

**Provenance verified with a fresh fetch** — same command block and output as
`l3_project-context-page-layout_ELITEA-2266.md` § Concrete Handles.

## Coverage Map

### Axis 1 — every case element

| # | Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|---|
| 1 | Navigate to Settings → Project Context | page loads | Step 2 | toggle card visible | covered |
| 2 | Turn the Project Context toggle OFF | no error, state shown | Step 3 | `PUT` 200 + unchecked + banner visible | covered |
| 3 | Clear all content from the Project Background editor | no error | Steps 4-5 (decomposed: reach the editor by URL, then clear) | editor text `""`, counter `2500 characters left.` | covered; **route reached by direct URL because Edit is disabled when OFF** — declared, #1793 |
| 4 | Click Save | responds | Step 6 | real click on `project-context-save-button` | covered |
| 5 | Verify the settings save without error | saved, no error | Step 6 | `PUT` 200 + toast `Project Context saved` + URL leaves `/edit` + no console errors | covered |
| 6 | Turn the Project Context toggle ON | no error | Steps 7-8 (phase B re-establishes content, then asserts the toggle is ON) | `project-context-enable-toggle` checked, banner count 0 | covered as an independent phase — **not in sequence**, because after step 5 no toggle exists (#1793) |
| 7 | Clear all content from the Project Background editor | no error | Steps 9-10 | editor text `""`, Save enabled | covered |
| 8 | Click Save | responds | Step 11 | real click | covered |
| 9 | Verify the settings save without error | saved, no error | Step 11 | `PUT` 200 + toast + empty state renders | covered |
| P | Precondition: user logged in | — | Setup | `auth_state` | covered |
| P2 | (implicit) a Project Context exists | — | Setup A / Setup B | seeded via `PUT` | covered — not stated by the case; without it there is no toggle and no content to clear |

### Axis 2 — observables asserted beyond the case

| Observable | Why |
|---|---|
| `project-context-edit-button` **disabled** while OFF (step 3) and **enabled** while ON (step 9) | This is the live fact that makes the re-ordering necessary. Asserting both branches makes the workaround visible and test-enforced, so if the product later enables Edit when OFF the test says so instead of the workaround quietly outliving its reason. |
| The empty state renders and the toggle count is **0** after each empty save | The case's own step 6 assumes the opposite. Asserting the real post-save state pins #1793's behaviour, so a fix (toggle shown in the empty state) turns this test red and prompts the case to be re-ordered back. |
| `PUT` status 200 on every save | "Saves without error" needs a real success signal; the product's own response is the honest one, and it distinguishes "the toast rendered" from "the server accepted it". |
| Toast text `Project Context saved`, exact | Distinguishes the success path from `handleSave`'s `catch` branch, which toasts `Failed to save Project Context` — a weaker "a toast appeared" assertion would pass on failure. |
| Save **disabled** before the clear, **enabled** after (step 4 → 5) | Control condition proving the clear actually dirtied the editor rather than the button merely being clickable all along. |
| Char counter `2500 characters left.` after the clear | An independent second reading of "the editor is empty", from a different element driven by the same CodeMirror transaction. |

## Known Defects

- **#1793 (primary)** — the toggle is unreachable once content is empty; the Edit
  affordance is disabled when OFF while the `/edit` route is unguarded; a re-created
  context silently inherits `enabled: false`. All three confirmed live 2026-08-26. This
  is the reason for the declared re-ordering. Filed as a **clarification/question**, not
  a `bug`: no step produced an error and no assertion in this AFS fails — the case's
  step *order* is what the product contradicts.
- **#1794 (suite, pre-existing)** — `ProjectContextPage.click_create()` still waits for
  the retired `?view=create` URL and times out (reproduced live). **RESOLVED during
  implementation** (2026-08-26): the page object and the merged ELITEA-2272 spec both
  now pin `/settings/project-context/edit`.
- **#1792** — case-text layout drift.

## Blocked Steps
None — every case element above was executed live and observed. The two divergences
(direct-URL editor access; phase-B re-ordering) are declared in § Classification note
and asserted explicitly, not worked around silently.
