# Test Case: Sound Notifications — toggle and volume slider are interactive

## Metadata
- **TMS ID**: ELITEA-2386
- **Priority**: l3 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids` @ `36733706`, DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, batch `settings-w08`, cluster ELITEA-2385/2386/2388/2389, 2026-08-29
- **Status**: ready-for-automation (no defects on this control — all 7 steps passed live)
- **Surface digest**: `test-specs/settings-user-profile/_surface.md` → `_surface/personalization-family.md`
- **Clarification**: EliteaAI/elitea-testing-public#1967 (route drift + "disabled or hidden")

## Case-text drift — this spec asserts the LIVE contract

Both **case-text stale, product correct** (reverse-masking guard). Filed as #1967.

1. **"Navigate to Personalization → SOUND NOTIFICATIONS section"** — `/settings/personalization`
   404s. The section is on **Settings → Preferences** (`/settings/preferences`), accordion
   `sound-notifications-section`.
2. **Step 5 "Verify the Volume slider is disabled or hidden"** — the product **unmounts**
   it. `SoundNotificationControls.jsx` guards *both* the slider and the `Preview Sound`
   button with `{config.enabled && …}`, so turning the toggle off removes them from the
   DOM entirely; nothing is ever rendered-but-disabled. The case's "or hidden" branch is
   satisfied — assert **`to_have_count(0)`**, never `to_be_disabled()`.

## Not already covered — checked

`automation/tests/ui/settings/test_settings_sections_collapse_expand.py` (ELITEA-2372, on
batch trunk) uses `sound-notifications-section-header` / `sound-notifications-content` as a
collapse/expand probe only — it asserts the accordion body's *visibility*, never the toggle,
the slider or the preview button. Grep of `automation/tests/` for `sound` finds nothing
else. Fresh spec.

## Preconditions
- User is logged in (`auth_state`; localhost bypass).
- **State lives in `localStorage`**, key `elitea_ui.sound_notifications`
  (`{"enabled":bool,"volume":float}`) — a pytest browser context is fresh per run, so
  **no teardown, no shared-account pollution**.
- **Read-before-write on the toggle.** Observed live `enabled: true, volume: 0.5`, but the
  starting state is whatever the context restores; the spec asserts the *transition*
  (ON→OFF→ON), so it must read the initial `checked` value and, if it starts OFF, turn it
  ON first — never hardcode "starts enabled".

## Test Data
### read-live (no fixture data required)
| Field | Value |
|---|---|
| Volume slider range | `min=0 max=1 step=0.05`; marks `0% / 50% / 100%` |
| Volume observed at session start | `0.5` |

## Test Steps

1. **Case step 1 — open the section.** Navigate to `${BASE_URL}/settings/preferences`.
   - **Verify**: URL is `${BASE_URL}/settings/preferences`;
     `settings-nav-item-preferences` has `data-active="true"`;
     `sound-notifications-section` is visible and
     `sound-notifications-section-header` has `aria-expanded="true"`;
     `sound-notifications-content` is visible.
   - Read `sound-notifications-toggle-input`'s checked state; if unchecked, click
     `sound-notifications-toggle` once so the case starts from the ON state its steps 4–6
     assume, and re-assert checked.

2. **Case step 2 — the "Play sound when tasks complete" toggle is present.**
   - **Verify**: `sound-notifications-toggle` is visible;
     `sound-notifications-toggle-input` is enabled and **checked**.
   - **Verify**: `sound-notifications-content` contains the text
     `Play sound when tasks complete` (pins the toggle's own label — the section heading
     text is the different string `Sound Notifications`).

3. **Case step 3 — the Volume slider is present with range 0% to 100%.**
   - **Verify**: `sound-notifications-volume-slider-input` has `min="0"`, `max="1"`,
     `step="0.05"`.
   - **Verify**: `sound-notifications-volume-slider` renders mark labels `0%`, `50%`, `100%`.

4. **Case step 4 — toggle "Play sound when tasks complete" OFF.**
   Click `sound-notifications-toggle`.
   - **Verify**: `sound-notifications-toggle-input` is **not checked**.

5. **Case step 5 — the Volume slider is disabled or hidden.**
   - **Verify**: `sound-notifications-volume-slider` has **count 0** (unmounted).
   - **Verify (beyond the case)**: `sound-notifications-preview-button` also has **count 0**
     — the same `config.enabled &&` guard removes it, and a build that hid the slider but
     left a live Preview Sound button would be a real defect this case would otherwise miss.
   - **Verify**: `sound-notifications-content` is still visible and still shows
     `Play sound when tasks complete` — i.e. the *section* did not collapse, only its
     conditional children unmounted. (Two different hide mechanisms live on this surface;
     see § Automation Hints.)

6. **Case step 6 — toggle back ON, the Volume slider is re-enabled.**
   Click `sound-notifications-toggle`.
   - **Verify**: `sound-notifications-toggle-input` is checked.
   - **Verify**: `sound-notifications-volume-slider` count 1, visible;
     `sound-notifications-volume-slider-input` is **enabled**.
   - **Verify (beyond the case)**: the slider's value is the same one it held before
     step 4 — an off/on cycle must not silently reset the user's volume.

7. **Case step 7 — "Preview Sound" is clickable.**
   - **Verify**: `sound-notifications-preview-button` is visible and enabled.
   - Do **not** click it — `playCompletionSound()` plays audio; "clickable" is fully
     established by visible + enabled.

8. **Beyond the case — the volume slider really is interactive** (the case *title* claims
   it, the case *steps* only check presence).
   Drag `sound-notifications-volume-slider-thumb` to **`0%` first and then to `50%`** of
   `sound-notifications-volume-slider`'s bounding box.
   - **Verify**: after each drag, `sound-notifications-volume-slider-input` has the exact
     value (`"0"`, then `"0.5"`) and the matching `aria-valuenow`.
   - *Amended during implementation (2026-08-29):* the AFS originally specced a single drag
     to 50%. Step 6 asserts the volume is *preserved* across the OFF/ON cycle, so whatever
     value the browser context restores is still in place here — and a slider already
     sitting at 50% would make a single drag-to-50% prove nothing. Two drags make the
     assertion falsifiable regardless of the starting value, at no extra cost.

9. **Beyond the case — no unexpected console errors.**
   - **Verify**: zero console errors. `/settings/preferences` logs none (verified live).
     **Do not add the #1771 filter here** — that would be masking on this route.
     Use `utils/console_errors.collect_console_errors(page)`.

## Expected Results
| # | Observable | Expected |
|---|---|---|
| 1 | route + accordion | `/settings/preferences`; section + content visible; `aria-expanded="true"` |
| 2 | toggle | visible, enabled, checked; label text `Play sound when tasks complete` |
| 3 | volume slider input | `min=0 max=1 step=0.05`; marks `0% 50% 100%` |
| 4 | toggle after click | unchecked |
| 5 | slider + preview after OFF | both count **0**; content still visible |
| 6 | after ON again | toggle checked; slider count 1, enabled; value preserved |
| 7 | Preview Sound | visible + enabled |
| 8 | slider after two drags | value `0` then `0.5`, matching `aria-valuenow` each time |
| 9 | console | 0 errors |

## Handles Reference (testid-only)

| Element | Testid | Provenance (verified 2026-08-29 after `git fetch origin`) |
|---|---|---|
| Preferences nav item | `settings-nav-item-preferences` | dynamic `SETTINGS_NAV_ITEM` constant; on `automation/testids` |
| Section wrapper | `sound-notifications-section` | on `automation/testids` only (awaiting human promotion to main) |
| Section header | `sound-notifications-section-header` | on `automation/testids` only |
| Section body | `sound-notifications-content` | on `automation/testids` only |
| Toggle (clickable `SwitchBase` span) | `sound-notifications-toggle` | **added** EliteaAI/EliteaUI@2d5f38d8 (`automation/testids`; not yet on `main`) |
| Toggle checkbox input | `sound-notifications-toggle-input` | **added** EliteaAI/EliteaUI@e087c0df — via `slotProps.input`, NOT `inputProps` (see the amended note below) |
| Volume slider root | `sound-notifications-volume-slider` | **added** EliteaAI/EliteaUI@2d5f38d8 (`automation/testids`; not yet on `main`) |
| Volume slider input | `sound-notifications-volume-slider-input` | **added** EliteaAI/EliteaUI@2d5f38d8 (`automation/testids`; not yet on `main`) |
| Volume slider thumb | `sound-notifications-volume-slider-thumb` | **added** EliteaAI/EliteaUI@2d5f38d8 (`automation/testids`; not yet on `main`) |
| Preview Sound button | `sound-notifications-preview-button` | **added** EliteaAI/EliteaUI@2d5f38d8 (`automation/testids`; not yet on `main`) |

### How to add them (zero-functional-impact)

All in `EliteaUI` `src/[fsd]/features/settings/ui/sound-notification/SoundNotificationControls.jsx`
— **pure prop/attribute additions, no new DOM node, no new hook**:

- `<Switch.BaseSwitch … data-testid="sound-notifications-toggle"
  slotProps={{ switch: { slotProps: { input: { 'data-testid': 'sound-notifications-toggle-input' } } } }} />`.
  `BaseSwitch` spreads `restProps` onto MUI's `Switch`, which puts `data-testid` on the
  `SwitchBase` **span**.
  ⚠️ **Amended during implementation (2026-08-29) — `inputProps` does NOT work.** This AFS
  originally specced `inputProps={{ 'data-testid': … }}`; it was implemented, and the input
  came back **without** the attribute. MUI v7's `Switch` builds its own
  `slotProps={{ input: mergeSlotProps(slotProps.input, { role: 'switch' }) }}` and hands that
  to `SwitchBase`, whose `{ input: inputProps, ...slotProps }` merge lets the constructed
  object win — so `inputProps` is dead on this component. The hidden checkbox must be
  addressed through `slotProps.input`, and because `BaseSwitch` consumes its own `slotProps`
  and spreads `slotProps.switch` onto the MUI `Switch`, that is one level in. Verified live.
  ⚠️ Both handles are needed: `to_be_checked()` only works on the input, and clicking the
  input is not what a user does — click the span (same split the existing
  `context-management-toggle` documents in the digest).
- `<Slider … data-testid="sound-notifications-volume-slider"
  slotProps={{ input: { 'data-testid': '…-volume-slider-input' },
  thumb: { 'data-testid': '…-volume-slider-thumb' } }} />`.
- `<Button.BaseBtn … data-testid="sound-notifications-preview-button">` — `BaseBtn`
  already spreads props (digest, `_surface/profile-and-drawer.md`).
- The component is feature-local with a **single consumer**, so feature-scoped testid names
  are correct here (the shared-component rule does not apply).

## Automation Hints

- **Two different hide mechanisms on this one page — pick per control, not per page.**
  A collapsed *accordion* keeps its children mounted and hides them with
  `visibility: hidden` ⇒ `not_to_be_visible()`. This toggle *conditionally unmounts*
  ⇒ `to_have_count(0)`. Using the wrong one is a silent false pass.
- **Do not drag onto a mark label.** Verified live on this exact slider: dragging the thumb
  onto the `100%` label landed on **0.95**, because the outer mark labels are
  `translateX(0)` / `translateX(-100%)`-shifted. Use a computed x on the slider root's
  bounding box.
- **Prefer drag over arrow keys** on any slider in this family — defect #1966 (keyboard
  arrows accumulate floating-point error). Not asserted by this spec.
- **Page object**: extend `automation/pages/settings_personalization_page.py`, which already
  owns `sound_notifications_section` / `_header` / `_content` and `PREFERENCES_PATH`.
  New locators are class-level `LocatorDescriptor` fields.
- **Markers**: `ui`, `settings`, `p3`, `regression`. No chat, no LLM — expect < 15 s.

## Known Defects
None on this control. All 7 case steps passed live on 2026-08-29
(toggle ON→OFF→ON, slider unmount/remount, Preview Sound enabled, 0 console errors).
Defects #1965/#1966 belong to the neighbouring Voice Personalization section (ELITEA-2385).

## Coverage Map

### Axis 1 — every element of the TMS case
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` | fixture | covered (setup) |
| Step 1 navigate to SOUND NOTIFICATIONS | section loads | Step 1 | URL + `data-active` + section/content visible + `aria-expanded` | covered (route corrected — #1967) |
| Step 2 toggle present | condition holds | Step 2 | toggle visible, enabled, checked + label text | covered |
| Step 3 Volume slider present, range 0–100% | condition holds | Step 3 | `min/max/step` + mark labels | covered |
| Step 4 toggle OFF | expected UI state | Step 4 | input not checked | covered |
| Step 5 slider disabled or hidden | condition holds | Step 5 | slider count 0 (+ preview count 0, + content still visible) | covered (**"disabled" branch never occurs** — unmount; clarification #1967) |
| Step 6 toggle ON → slider re-enabled | expected UI state | Step 6 | checked; slider count 1 + enabled + value preserved | covered |
| Step 7 "Preview Sound" is clickable | condition holds | Step 7 | visible + enabled | covered (deliberately not clicked) |
| Expected final state: Preview Sound clickable | — | Step 7 | same | covered |

### Axis 2 — asserted beyond the case
| Observable | Why |
|---|---|
| `sound-notifications-preview-button` also unmounts at step 5 | the same `config.enabled &&` guard controls it; a build that hid the slider but left a live Preview Sound button is a real regression the case's wording would miss |
| section content still visible at step 5 | separates "the toggle unmounted its children" from "the accordion collapsed" — the two mechanisms are visually similar and only one is under test |
| volume value preserved across the OFF→ON cycle (step 6) | an unmount/remount that resets the user's setting is a classic conditional-render bug; the case's "re-enabled" wording does not pin it |
| slider drag to 0% then 50% (step 8) | the case *title* asserts the volume slider is **interactive**, but no step ever moves it — presence alone would let a frozen slider pass; two drags keep it falsifiable whatever value the context restores |
| 0 console errors (step 9) | this route is verified clean, so any error is signal |
