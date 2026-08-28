# Test Case: Voice Personalization — Voice dropdown, Speed and Volume sliders are interactive

## Metadata
- **TMS ID**: ELITEA-2385
- **Priority**: l3 (case priority `medium`)
- **Environment Explored**: local (`http://localhost:5173`, `EliteaAI/EliteaUI` `automation/testids` @ `36733706`, DEV backend)
- **User set**: `${TEST_USER}` (localhost `auth_state` bypass via `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, batch `settings-w08`, cluster ELITEA-2385/2386/2388/2389, 2026-08-29
- **Status**: ready-for-automation (**sanctioned-RED** — one soft-asserted, linked product defect; see § Known Defects)
- **Surface digest**: `test-specs/settings-user-profile/_surface.md` → `_surface/personalization-family.md`
- **Defects filed**: EliteaAI/elitea-testing-public#1965 (blank Voice dropdown — **soft-asserted here**), EliteaAI/elitea-testing-public#1966 (keyboard float noise — not asserted, see § Known Defects)
- **Clarification**: EliteaAI/elitea-testing-public#1967 (route drift + the "Mute" mark)

## Case-text drift — this spec asserts the LIVE contract

Both rows are **case-text stale, product correct** (reverse-masking guard — do not
assert the stale text). Filed as clarification #1967, not as defects.

1. **"Navigate to Personalization → VOICE PERSONALIZATION section"** — `/settings/personalization`
   returns the app's global *"Page not found"* view. The section lives on
   **Settings → Preferences** (`/settings/preferences`), accordion
   `voice-personalization-section`.
2. **Step 7 "Volume slider … range Mute to 100%"** — the control's marks are
   **`0%` / `50%` / `100%`**; the word *Mute* appears nowhere on it
   (`VOICE_VOLUME_MARKS`, `EliteaUI` `src/[fsd]/features/chat/voice-config/constants/voice.constants.js`).
   Assert `0%`.

## Not already covered — checked

Greps by behaviour over `test-specs/` and `automation/tests/`:
`automation/tests/ui/voice/test_voice_configuration.py` is the **chat voice-mode dialog**
(`VoiceConfigDialog`), not the Preferences accordion — different route, different mount,
different observables. `automation/tests/ui/settings/test_settings_sections_collapse_expand.py`
(ELITEA-2372) touches `voice-personalization-section-header` only as an accordion
collapse probe and asserts nothing about the controls inside. No spec anywhere asserts the
Voice select, either slider, or `voice-preview-button`. Fresh spec.

## Preconditions
- User is logged in (`auth_state`; localhost bypass).
- **State lives in `localStorage`, not on the account** — key `elitea_voice_config`
  (`useVoiceConfig.hooks.js`, `{voiceName, voiceId, rate, volume}`). A pytest browser
  context is fresh per run, so **no teardown and no shared-account pollution**: this is
  the rare settings spec that mutates nothing another spec reads.
- The Voice dropdown is populated from **model TTS** voices
  (`GET …/configurations/…/tts` via `useGetTtsVoicesQuery`) whenever a TTS model + socket
  are available; otherwise from `window.speechSynthesis.getVoices()`, which is typically
  **empty in headless Chromium** and makes the select disappear entirely
  (`voiceOptions.length > 0 &&` guard). Observed live: the model-TTS branch, 9 options.
  ⇒ The spec must **assert the select is present** and fail loudly rather than skip if it
  is not — a vanished select means the TTS model config changed, which is real signal.

## Test Data
### read-live (no fixture data required)
| Field | Value |
|---|---|
| Voice options observed | `alloy, ash, coral, echo, fable, nova, onyx, sage, shimmer` (9, model TTS) |
| Voice selected by the spec | `nova` (any option other than the current one) |
| Speed target | `1.5` (case step 6) — slider range `min=0.5 max=2 step=0.1` |
| Volume target | `0.5` (case step 8) — slider range `min=0 max=1 step=0.05` |

## Test Steps

1. **Case step 1 — open the section.** Navigate to `${BASE_URL}/settings/preferences`.
   - **Verify**: URL is `${BASE_URL}/settings/preferences`;
     `settings-nav-item-preferences` has `data-active="true"`;
     `voice-personalization-section` is visible;
     `voice-personalization-section-header` has `aria-expanded="true"`
     (`BasicAccordion` `defaultExpanded` is `true`).

2. **Case step 2 — the Voice dropdown is present and shows a selected option.**
   - **Verify (hard)**: `voice-personalization-voice-select-combobox` is visible.
   - **Verify (SOFT — `expect.soft`, `# Known defect: #1965`)**: the combobox has
     non-empty text, i.e. a voice is actually selected. **Live it is blank** on a fresh
     browser profile — assert the *correct* expected behaviour, never the broken one
     (`.agents/testing.md` § Merge gate, analysis-time sanctioned-RED entry).

3. **Case step 3 — open the dropdown, a list of voices appears.**
   Click `voice-personalization-voice-select-combobox`.
   - **Verify**: the option collection `[data-testid^="select-option-"][data-selected]`
     has **count ≥ 1** and `select-option-nova` is visible.
     *(The `[data-selected]` attribute filter is mandatory: `SingleSelectMenuItem.jsx:141`
     renders a nested `select-option-selected-icon` inside the selected row, which a bare
     prefix match would count as an extra element — see § Automation Hints.)*
   - Do **not** assert an exact option count: the list is backend-supplied TTS voices, not
     a front-end constant, so an exact count is a false-red waiting to happen.

4. **Case step 4 — select a different voice.** Click `select-option-nova`.
   - **Verify**: `voice-personalization-voice-select-combobox` has text `Nova`;
     `select-option-*` list has closed (`select-option-nova` count 0 / not visible).

5. **Case step 5 — the Speed slider is present with range 0.5x to 2x.**
   - **Verify**: `voice-personalization-speed-slider-input` has attribute `min="0.5"`,
     `max="2"`, `step="0.1"`.
   - **Verify**: the slider's mark labels read `0.5x, 1x, 1.5x, 2x`
     — assert against `voice-personalization-speed-slider` (the accordion is expanded, so
     the labels are visible).

6. **Case step 6 — drag the Speed slider to 1.5x.**
   Drag from `voice-personalization-speed-slider-thumb` to the x-coordinate
   `box.x + box.width * (1.5-0.5)/(2-0.5)` of `voice-personalization-speed-slider`'s
   bounding box (see § Automation Hints — **drag, not arrow keys**).
   - **Verify**: `voice-personalization-speed-slider-input` has value `"1.5"`.
   - **Verify**: `voice-personalization-speed-slider-input` has attribute
     `aria-valuenow="1.5"` — this is what pins the drag path as clean and would catch
     #1966 leaking into it.

7. **Case step 7 — the Volume slider is present with range 0% to 100%.**
   - **Verify**: `voice-personalization-volume-slider-input` has `min="0"`, `max="1"`,
     `step="0.05"`.
   - **Verify**: its mark labels read `0%, 50%, 100%` (**not** "Mute" — case-text drift).

8. **Case step 8 — drag the Volume slider to 50%.**
   Drag `voice-personalization-volume-slider-thumb` to `box.x + box.width * 0.5`.
   - **Verify**: `voice-personalization-volume-slider-input` has value `"0.5"` and
     `aria-valuenow="0.5"`.

9. **Case step 9 — "Preview Voice" is clickable.**
   - **Verify**: `voice-preview-button` is visible and enabled.
   - Do **not** click it. It calls `useTextToSpeech().speak()`, which either opens a socket
     TTS stream or drives `speechSynthesis` — audible, slow, and it *unmounts the button*
     while playing (`{!isPlaying && …}`). "Clickable" is fully established by
     visible + enabled; clicking adds an LLM/socket-shaped flake for no extra evidence.

10. **Beyond the case — no unexpected console errors.**
    - **Verify**: zero console errors across the whole run.
      `/settings/preferences` logs **none** (verified live; unlike `/settings/memory` and
      `/settings/ai-personality`, which log the known #1771 `disableUnderline` warning).
      **Do not add the #1771 filter to this spec** — on this route it would be masking.
      Use `utils/console_errors.collect_console_errors(page)` so a future failure carries
      the resource URL.

## Expected Results
| # | Observable | Expected |
|---|---|---|
| 1 | route + accordion | `/settings/preferences`, `voice-personalization-section` visible, `aria-expanded="true"` |
| 2 | Voice combobox | visible; **soft**: non-empty selected text (`#1965` — currently blank) |
| 3 | option list | ≥1 `select-option-*` row; `select-option-nova` visible |
| 4 | Voice combobox after select | text `Nova` |
| 5 | Speed slider input | `min=0.5 max=2 step=0.1`; marks `0.5x 1x 1.5x 2x` |
| 6 | Speed slider after drag | value `1.5`, `aria-valuenow="1.5"` |
| 7 | Volume slider input | `min=0 max=1 step=0.05`; marks `0% 50% 100%` |
| 8 | Volume slider after drag | value `0.5`, `aria-valuenow="0.5"` |
| 9 | Preview Voice | visible + enabled |
| 10 | console | 0 errors |

## Handles Reference (testid-only — `.agents/testing.md` § Locator policy)

| Element | Testid | Provenance (verified 2026-08-29 after `git fetch origin`) |
|---|---|---|
| Preferences nav item | `settings-nav-item-preferences` | dynamic pattern `SETTINGS_NAV_ITEM` already in `SettingsPersonalizationPage`; on `automation/testids` |
| Section wrapper | `voice-personalization-section` | **on-main ✓** (also on `automation/testids`) |
| Section header | `voice-personalization-section-header` | on `automation/testids` only (awaiting human promotion to main) |
| Preview Voice button | `voice-preview-button` | **on-main ✓** |
| Voice select | `voice-personalization-voice-select` | **added** EliteaAI/EliteaUI@2d5f38d8 (`automation/testids`; not yet on `main`) |
| Voice select display | `voice-personalization-voice-select-combobox` | **derived automatically** by `SingleSelect` from the `data-testid` above (`SingleSelect.jsx:82,661-662`) — no separate add |
| Voice option row | `[data-testid="select-option-{}"]` (class constant, `.format(value)`) | **on-main ✓** — shared generic testid from `SingleSelectMenuItem.jsx:416` |
| Option-row collection | `[data-testid^="select-option-"][data-selected]` (class constant) | as above |
| Speed slider root | `voice-personalization-speed-slider` | **added** EliteaAI/EliteaUI@2d5f38d8 (`automation/testids`; not yet on `main`) |
| Speed slider input | `voice-personalization-speed-slider-input` | **added** EliteaAI/EliteaUI@2d5f38d8 (`automation/testids`; not yet on `main`) |
| Speed slider thumb | `voice-personalization-speed-slider-thumb` | **added** EliteaAI/EliteaUI@2d5f38d8 (`automation/testids`; not yet on `main`) |
| Volume slider root | `voice-personalization-volume-slider` | **added** EliteaAI/EliteaUI@2d5f38d8 (`automation/testids`; not yet on `main`) |
| Volume slider input | `voice-personalization-volume-slider-input` | **added** EliteaAI/EliteaUI@2d5f38d8 (`automation/testids`; not yet on `main`) |
| Volume slider thumb | `voice-personalization-volume-slider-thumb` | **added** EliteaAI/EliteaUI@2d5f38d8 (`automation/testids`; not yet on `main`) |

### How to add the six slider testids + the select testid (zero-functional-impact)

> **Amended during implementation (2026-08-29):** all seven were added exactly as
> described below — pure prop additions, 19 added lines, 0 removals, no new DOM node
> and no new hook (EliteaAI/EliteaUI@2d5f38d8). The `slotProps.input` / `slotProps.thumb`
> forwarding was verified live on MUI v7.

All in `EliteaUI` `src/[fsd]/features/chat/voice-config/ui/VoiceConfigControls.jsx` —
**pure prop/attribute additions, no new DOM node, no new hook** (`add-data-testid` § Step 5.5):

- `<SingleSelect … data-testid="voice-personalization-voice-select" />` — the component
  already accepts `data-testid` and emits `${dataTestId}-combobox` on the display element.
- Each `<Slider …>` gets
  `data-testid="voice-personalization-<speed|volume>-slider"` **plus**
  `slotProps={{ input: { 'data-testid': '…-slider-input' }, thumb: { 'data-testid': '…-slider-thumb' } }}`.
  MUI v5 `Slider` forwards `slotProps.input` / `slotProps.thumb` to the hidden
  `<input type="range">` and the thumb `<span>` respectively.
- Mark labels are **not** given testids — assert them through the slider-root testid's
  text (they are that element's own rendered text), never via a `.MuiSlider-markLabel`
  CSS hop.

## Automation Hints

- **Drag, never arrow keys.** Verified live both ways: a drag lands exactly on the step
  grid (`1.5`, `aria-valuenow="1.5"`), whereas five `ArrowRight` presses land on
  `1.5000000000000004` and paint `1.5000000000000004×` in the value label (defect #1966 —
  MUI's keyboard handler adds `step` without re-rounding, its pointer handler routes
  through `roundValueToStep`). The case says *drag*; use drag.
- **Do not drag onto a mark label.** Verified live: dragging the sound-volume thumb onto
  the `100%` label landed on **0.95**, because the first and last mark labels are
  `translateX(0)` / `translateX(-100%)`-shifted, so their centre is not the track position.
  Interior labels happen to line up, but the reliable form is a computed x on the slider
  root's bounding box (and it needs no extra handle).
- **`input.value` hides the float artifact** (the DOM normalises `1.5000000000000004` to
  `"1.5"`), so a value-only assertion cannot detect it — that is why step 6 also pins
  `aria-valuenow`.
- **The `[data-selected]` filter on the option collection is mandatory** — see step 3.
- **Page object**: extend `automation/pages/settings_personalization_page.py`
  (`SettingsPersonalizationPage` already owns `PREFERENCES_PATH`,
  `voice_personalization_section`, `voice_personalization_header`, `voice_preview_button`
  and `open_settings_tab()`); add the new `LocatorDescriptor` class fields there, plus a
  `drag_slider_to(fraction)` helper. Locators stay class-level fields — never built in a
  method body.
- **Markers**: `ui`, `settings`, `p3`, `regression`. Runtime is short (no chat, no LLM);
  expect < 15 s.

## Known Defects

| # | Defect | Handling in this spec |
|---|---|---|
| #1965 | Voice dropdown renders blank on a fresh profile — the `alloy` default effect is dead (`config?.voiceId !== undefined` guard vs `DEFAULT_CONFIG.voiceId = null`) | Step 2's selected-option check is written as the **correct** expectation with `expect.soft()` + `# Known defect: #1965`. Deterministic, single-cause, linked-to-open ⇒ **sanctioned-RED**: `expect.soft` failures ARE pytest failures, so this spec's gate signature is *one* soft failure, 3/3 identical, and the case stays `blocked-on-#1965` until the fix lands. |
| #1966 | Keyboard arrows produce floating-point noise on both sliders (drag path clean) | **Not asserted.** The case's interaction is a drag, which is correct; asserting a keyboard artifact the case never exercises would add a second permanent red for behaviour outside the case. Recorded here so a future keyboard-driven variant does not re-litigate it. |

## Coverage Map

### Axis 1 — every element of the TMS case
| Case element | Expected result | Covered by | Asserted where | Disposition |
|---|---|---|---|---|
| Precondition: user logged in | — | `auth_state` | fixture | covered (setup) |
| Step 1 navigate to VOICE PERSONALIZATION | section loads | Step 1 | URL + `data-active` + section visible + `aria-expanded` | covered (route corrected — clarification #1967) |
| Step 2 dropdown present, shows a selected option | condition holds | Step 2 | combobox visible (hard) + non-empty text (soft) | **covered, currently RED** — defect #1965 |
| Step 3 click dropdown → option list appears | control responds | Step 3 | option collection ≥1, `select-option-nova` visible | covered |
| Step 4 select a different voice | next state shown | Step 4 | combobox text `Nova`, list closed | covered |
| Step 5 Speed slider present, range 0.5x–2x | condition holds | Step 5 | `min/max/step` attrs + mark labels | covered |
| Step 6 drag Speed to 1.5x | expected UI state | Step 6 | value `1.5` + `aria-valuenow` | covered |
| Step 7 Volume slider present, range Mute–100% | condition holds | Step 7 | `min/max/step` + marks `0% 50% 100%` | covered (**"Mute" is case-text drift** — clarification #1967) |
| Step 8 drag Volume to 50% | expected UI state | Step 8 | value `0.5` + `aria-valuenow` | covered |
| Step 9 "Preview Voice" is clickable | condition holds | Step 9 | visible + enabled | covered (deliberately not clicked — rationale in the step) |
| Expected final state: Preview Voice clickable | — | Step 9 | same | covered |

### Axis 2 — asserted beyond the case
| Observable | Why |
|---|---|
| `aria-expanded="true"` on the section header (step 1) | distinguishes "section rendered but collapsed" from "section ready"; a collapsed accordion keeps children mounted (`visibility: hidden`), so a naked presence check would pass on a collapsed section |
| `aria-valuenow` on both sliders (steps 6, 8) | `input.value` is DOM-normalised and would silently swallow defect #1966 if the pointer path ever regressed to the keyboard path's arithmetic |
| option list closes after selection (step 4) | a select that leaves its popover open is a real regression the case's "control responds" wording does not pin |
| 0 console errors (step 10) | this route is verified clean, so any error is signal, and the URL-carrying collector turns a future occurrence into a filable report |
