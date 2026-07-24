# Test Case: Settings — Preferences: Theme Toggle Switches Light/Dark and Persists Across Reload

## Metadata
- **TMS ID**: GAP-020
- **Linked Story**: none
- **Priority**: l4 (low — as authored on the board)
- **Environment Explored**: local (`http://localhost:5173`, EliteaUI `automation/testids`
  branch → DEV backend, project `Private`)
- **User set**: `${TEST_USER}` (on localhost, `auth_state` fixture skips login via
  `VITE_DEV_TOKEN`)
- **Analyst**: qa-engineer, analyst slot
- **Status**: **ready-for-automation** — case executed end-to-end live at
  `/settings/preferences`, all 7 case steps observed (both switch directions +
  full-reload persistence), no product defects found. Two testid gaps
  (`preferences-theme-dark-toggle` / `preferences-theme-light-toggle`, exactly as
  the case's own Automation Notes already named them) are additive, well-scoped
  frontend work — per `.agents/role-overrides.md` § Analyst slot a testid gap
  alone never downgrades status.

## Preconditions
- User is logged in to the Elitea platform (on localhost, `auth_state` fixture
  skips login).
- Navigate to `${BASE_URL}/settings/preferences` directly — this is the real
  route for "Settings → PERSONAL → Preferences" (confirmed live; the page's own
  header reads "Preferences" and the drawer highlights the **Preferences** item).
  The **General** accordion (`PreferenceGeneral.jsx`, `BasicAccordion` with
  `defaultExpanded`) is expanded automatically on load — no click needed.
- Note `localStorage.getItem('mode')` before the run so it can be restored in
  cleanup. Confirmed live: on a session that never touched it, the key is
  **absent (`null`)**, not `"dark"` — the app defaults to Dark via
  `localStorage.getItem('mode') || 'dark'` (`src/slices/settings.js:76`), it
  does **not** pre-seed the key. Test setup must therefore branch on
  "key present → capture its value" vs "key absent → cleanup means removing the
  key again (`localStorage.removeItem('mode')`), not writing back the literal
  string `'dark'`" — writing `'dark'` explicitly would leave the browser storage
  in a state a fresh user never has.

## Test Data

### reuse-existing
- `localStorage` key: `mode` — values `'dark'` / `'light'` (exact strings written
  by `switchMode`, confirmed via `src/slices/settings.js:109-111`).
- Redux state path `state.settings.mode` mirrors the same value (not directly
  queryable from outside the app in this run — no `window.store` / Redux
  DevTools hook was found exposed on `window`; the externally-observable proxies
  below stand in for it).

No `generate-per-test` / `generate-shared-with-cleanup` data needed — this
case only flips a client-side preference, no entities are created.

## Test Steps

1. Navigate to `${BASE_URL}/settings/preferences`; wait for the **General**
   accordion / Theme label to render.
   - **Verify**: both toggle buttons render side by side under the "Theme"
     label, with accessible text `"Dark"` and `"Light"` respectively (case
     step 1).
2. Read `localStorage.getItem('mode')` and the buttons' `Mui-selected` class /
   `aria-pressed` attribute.
   - **Verify**: the button matching the stored mode (or **Dark**, if the key is
     absent) carries `class~="Mui-selected"` and `aria-pressed="true"`; the
     other button carries neither (case step 2). Confirmed live from a clean
     `mode`-unset state: **Dark** was selected (`aria-pressed="true"`,
     `Mui-selected` present), **Light** was not.
3. With the app in Dark, click the **Light** toggle button.
   - **Verify**: `localStorage.getItem('mode') === 'light'` (case step 3).
   - **Verify (palette)**: the app repaints — see the important behavioral note
     under § Concrete Handles ("Palette assertion — read this before asserting
     colors"); the practical assertion is `getComputedStyle(document.body)
     .backgroundColor` (or `document.documentElement` / `#root`, all three move
     together) changing from `"rgb(14, 19, 29)"` (Dark) to `"rgba(0, 0, 0, 0)"`
     (Light — transparent, i.e. the override is removed, not "set to a light
     color"). Confirmed live both directions.
   - **Verify (no backend call)**: no network request fires for this action —
     confirmed live via `get-network --status error` (empty) and a full
     network-log read across the click (zero new requests of any status). This
     is a pure client-side Redux + `localStorage` action.
4. Confirm the toggle's active state after switching to Light.
   - **Verify**: **Light** now carries `Mui-selected` / `aria-pressed="true"`;
     **Dark** carries neither (case step 4). Confirmed live.
5. Click the toggle again to flip back to Dark (click the **Dark** button).
   - **Verify**: `localStorage.getItem('mode') === 'dark'`; palette repaints
     back to `backgroundColor === "rgb(14, 19, 29)"`; **Dark** shows
     `Mui-selected` (case step 5). Confirmed live.
   - **Behavioral note (important — do not skip)**: MUI's `ToggleButtonGroup`
     is `exclusive` (`TabGroupButton.jsx`) — clicking the **already-selected**
     button reports `newValue === null` to `onChange`, and the handler's own
     guard (`if (newValue !== null) { … }`) **swallows that call entirely — no
     dispatch, no localStorage write, no repaint.** Confirmed live: clicking
     **Dark** a second time while already in Dark left `localStorage['mode']`
     and the selected class completely unchanged. The case's own Automation
     Note ("clicking either button flips the mode") is only true when the
     clicked button is **not** the currently-active one — automation must
     always click the **non-active** button to produce a flip, never assume
     "click Dark" always flips regardless of current state.
6. Switch to Light once more, then **reload the page** and reopen
   `${BASE_URL}/settings/preferences`.
   - **Verify**: after reload, `localStorage.getItem('mode') === 'light'`
     (unchanged — reload doesn't touch storage) and, once the app re-hydrates,
     **Light** shows `Mui-selected` and the palette is repainted light
     (`backgroundColor === "rgba(0, 0, 0, 0)"`) — confirmed live end-to-end: the
     SPA route survives a hard reload without redirecting away from
     `/settings/preferences`, and `state.settings.mode` seeds from
     `localStorage.getItem('mode') || 'dark'` on the fresh module load, so Light
     restores correctly (case step 6).
7. Cleanup: restore `localStorage['mode']` (and the visible toggle) to the value
   noted in step 2 — click the toggle needed to reach that mode (skip the click
   if already there, since clicking the active button is a no-op per step 5's
   note). If the original state was "key absent", removing the key directly
   (`localStorage.removeItem('mode')`) is safer/faster than reproducing the
   click sequence to nowhere (see Preconditions).

## Expected Results
- Each switch to the non-active button writes the correct value (`'light'` /
  `'dark'`) to `localStorage['mode']` and repaints the palette accordingly.
- Clicking the already-active button is a confirmed no-op (MUI exclusive
  `ToggleButtonGroup` semantics) — not a defect, a documented behavior.
- The active toggle button's `Mui-selected` class / `aria-pressed` attribute
  always tracks the current mode.
- The mode chosen before reload survives a full page reload.
- No network request accompanies any mode switch (pure client-side).
- No console errors at any step (confirmed live — `get-console` showed only
  informational/debug entries: React DevTools banner, the startup ASCII banner,
  Google Analytics init, socket.io connect — nothing at `error` level).

## Coverage Map

**Axis 1 — Case coverage**

| Case element | Expected result | Covered by (AFS step) | Asserted where | Disposition |
|---|---|---|---|---|
| 1 Both toggle buttons render under Theme label | Dark + Light buttons visible side by side | step 1 | step 1: accessible-text presence | asserted |
| 2 Read `localStorage['mode']` + selected button | matching button carries `.Mui-selected`; default unset → Dark selected | step 2 | step 2: class + aria-pressed read | asserted |
| 3 Click Light while in Dark | `switchMode` dispatched, `localStorage['mode']==='light'`, light palette applied | step 3 | step 3: localStorage read + `backgroundColor` read | asserted |
| 4 Confirm active state after switch | Light `.Mui-selected`, Dark not | step 4 | step 4: class read on both buttons | asserted |
| 5 Click again to flip back to Dark | `localStorage['mode']==='dark'`, dark palette, Dark `.Mui-selected` | step 5 | step 5: localStorage + class + `backgroundColor` read | asserted |
| 6 Switch to Light, reload, reopen | mode restored to Light from `localStorage`, Light selected, light palette | step 6 | step 6: post-reload localStorage + class + `backgroundColor` read | asserted |
| 7 Cleanup: restore original mode | app + `localStorage['mode']` back to starting state | step 7 (Cleanup) | step 7: localStorage read == original | asserted |
| Test Data: default (unset) mode is `dark` | app initializes Dark when key absent | step 2 | step 2: fresh-unset-key observation | asserted |

Disposition key: `asserted` | `already-covered` | `clarification` | `blocked` | `out-of-scope`.
No row falls outside `asserted` — nothing to list in § Blocked Steps / §
Known Defects beyond the testid gap (tracked as implementer work, not a
blocker — see Metadata § Status).

**Axis 2 — Analyst additions**

- Step 3 asserts **no network request fires** for a mode switch — *added:
  confirmed live via `get-network --status error` (empty) plus a full
  network-log read; guards against a future regression that makes theme
  switching depend on a backend round-trip (it shouldn't — it's pure Redux +
  `localStorage`).*
- Step 5 asserts **clicking the already-active button is a no-op** — *added:
  this is NOT in the original case text at all, but it is exactly the kind of
  assumption a naive "click Dark, expect flip" implementation would get wrong
  after step 5 (Dark is already active at that point going INTO step 7's
  restore-if-needed logic); guards against a false "flip" assumption.*
- Console-error check across every step — *added: standard side-channel
  discipline; confirmed clean (info/debug only, no `error`-level entries).*

## Cleanup
1. Restore `localStorage['mode']` to the value captured in Preconditions
   (or remove the key entirely if it was absent at the start) and leave the
   toggle showing the matching selected state.

## Concrete Handles (discovered during exploration)

**Palette assertion — read this before asserting colors.** The case text says
step 3's expected result is "the app repaints in the light palette (page/panel
backgrounds go light)" — read literally this suggests a set light RGB value.
Live inspection shows the *actual* mechanism: **Dark mode explicitly sets
`background-color: #0E131D` (`rgb(14, 19, 29)`, the theme's `gray60`,
`src/darkPalette.js`) on `document.body` / `document.documentElement` / `#root`
(all three move together); Light mode does NOT set an override at all** — it
leaves the property at its browser default (`rgba(0, 0, 0, 0)`, transparent),
which is what makes the page look light (nothing is painting over the
default white canvas). Assert the **transition** (`rgb(14, 19, 29)` ⇄
`rgba(0, 0, 0, 0)`), not a literal "light" color — asserting `backgroundColor
=== 'white'`/`'#fff'` would be a **false assumption that fails** even though
the behavior is correct.

| Element | Recommended Locator | Fallback / Notes |
|---|---|---|
| Dark toggle button | `testid needed: preferences-theme-dark-toggle` | **No fallback** — add via `add-data-testid` in `ThemeModeToggle.jsx` (see below). Raw value attribute `button[value="dark"]` was used ONLY for live exploration in this session, never for the implemented test. |
| Light toggle button | `testid needed: preferences-theme-light-toggle` | Same — `button[value="light"]` is exploration-only, not a locator to ship. |
| Selected-state filter (once testid exists) | `[data-testid="preferences-theme-dark-toggle"][class*="Mui-selected"]` / same for light | State via class filter on the stable testid, per `.agents/testing.md` § Locator policy — do not invent a separate `-selected`/`-active` testid variant. `aria-pressed="true"/"false"` is an equally valid state signal already present (MUI sets it natively on `ToggleButton`) if the reviewer prefers an ARIA-based assertion over class-matching; either is acceptable, pick one and be consistent. |
| Mode persistence | `localStorage.getItem('mode')` (Playwright: `page.evaluate("() => localStorage.getItem('mode')")`) | Values: `'dark'` \| `'light'` \| absent (`null`, treated as `'dark'`). |
| Palette signal | `getComputedStyle(document.body).backgroundColor` (or `document.documentElement`, or `#root` — confirmed to move together) | Dark → `"rgb(14, 19, 29)"`; Light → `"rgba(0, 0, 0, 0)"`. Via Playwright: `page.evaluate("() => getComputedStyle(document.body).backgroundColor")`. |
| General accordion / Theme section | `PreferenceGeneral.jsx`'s `BasicAccordion` item has **no** `testId`/`dataTestId` prop wired (confirmed via source read) | **Not needed for this case** — the Theme toggle buttons are unique page-wide once testid'd; scoping to the accordion adds nothing this test's own code path uses (canon ruling #511 — don't add a testid the test doesn't need). |

### Testid addition (implementer work — `add-data-testid`)

**File**: `EliteaUI/src/components/ThemeModeToggle.jsx` (confirmed on
`automation/testids`, single call site: `PreferenceGeneral.jsx` only — not a
shared component, so hardcoding is correct, no `testId` prop indirection
needed).

**Where**: the `themeArrayBtn` array (lines ~21–42) — add a `buttonProps` key
to each entry; `TabButtonItem.jsx` already spreads `{...item.buttonProps}` onto
the underlying `ToggleButton` (confirmed via source read, line 15), so this is
a clean, precedented integration point exactly as the case's own Automation
Notes describe:

```js
{
  value: ThemeModeOptions.Dark,
  buttonProps: { 'data-testid': 'preferences-theme-dark-toggle' },
  icon: (...),
  tooltip: 'Dark theme',
},
{
  value: ThemeModeOptions.Light,
  buttonProps: { 'data-testid': 'preferences-theme-light-toggle' },
  icon: (...),
  tooltip: 'Light theme',
},
```

Naming follows `{section}-{element}-{type}` (`preferences` section,
`theme-dark`/`theme-light` element, `toggle` type) — matches the case's own
proposed names verbatim, uniqueness not yet checked against the full
`automation/testids` inventory by this analyst (implementer should re-verify
per the standard `add-data-testid` step before committing).

## Network Behavior
None. Confirmed live: `get-network --status error` returned `[]` across every
mode switch, and a full network-log read showed zero new requests correlated
with any toggle click — `switchMode` is pure Redux state + `localStorage.setItem`
(`src/slices/settings.js:109-111`), no API round-trip.

## Known Defects Found During Exploration
None found. No console errors, no failed requests, no visual/behavioral defect.
(The MUI exclusive-toggle no-op behavior documented in step 5 is **not** a
defect — it is the correct, intentional MUI `ToggleButtonGroup` semantics for
an `exclusive` group and is called out purely so the automation doesn't
misinterpret a same-button re-click as a failed flip.)

## Blocked Steps
None. The two testid gaps are implementer work per Metadata § Status, not a
block on execution — every case step was executed and observed live using the
existing `value="dark"`/`value="light"` DOM attributes as a temporary
exploration-only handle (never intended to ship in the final test).

## Automation Hints

- **Page object**: extend `automation/pages/user_profile_settings_page.py`
  (`UserProfileSettingsPage`) — it already targets this exact route. **Naming
  trap in the existing code (pre-existing, not introduced by this case):**
  `navigate_to_personalization()` navigates to `/settings/preferences` (this
  case's page — Theme + Voice Personalization + Sound Notifications), while
  `navigate_to_profile()` navigates to `/settings/personalization` (a
  *different* page — Default Context Management). The names are swapped
  relative to what a reader would expect from the URLs; don't "fix" the
  swapped naming as part of this case (out of scope / would touch unrelated
  Voice/Context-Management tests that already depend on the current names) —
  just be aware of it and use `navigate_to_personalization()` for this case's
  target, exactly as `test_voice_configuration.py` already does for the same
  page.
- **Don't reuse `wait_for_personalization_load()` as this test's sole page-ready
  wait** — it waits on the `voice-personalization-section` testid AND the Voice
  dropdown (`#simple-select-Voice`) becoming visible, which depends on an async
  TTS-voices fetch **unrelated to Theme**. That coupling makes a
  Theme-only test wait on Voice's network round-trip for no reason. Prefer a
  lighter, Theme-scoped wait once the testids exist:
  `self.preferences_theme_dark_toggle.wait_for(state="visible")` (or a
  dedicated `wait_for_theme_section_load()` if the implementer wants a named
  method) — still call `navigate_to_personalization()` for the navigation
  itself, just don't block the whole test on Voice's readiness.
- **Reading the palette signal**: a bare `page.evaluate("() => getComputedStyle
  (document.body).backgroundColor")` is sufficient; no need to scroll or wait
  beyond the localStorage write settling (this is synchronous React state — no
  debounce, no autosave round-trip, unlike the neighboring Voice/Sound sections
  on the same page which DO autosave over the network).
- **Framework**: Playwright + pytest, per `.agents/testing.md` (no case-specific
  deviation).
- **Locator policy**: testid-only (`.agents/role-overrides.md` +
  `.agents/testing.md` § Locator policy) — the two `testid needed:` rows above
  are mandatory `add-data-testid` work, not a fallback to `button[value=...]` or
  any other raw selector in the shipped test.
