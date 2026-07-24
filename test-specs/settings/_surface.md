# Surface digest — Settings (`/settings/*`)

Seeded 2026-07-24 by GAP-020 analysis. Handle cache for the Settings drawer's
PERSONAL section — verify every handle below live before trusting it; this is
a cache, not a substitute for execution.

## Routing (confirmed live — non-obvious, read before navigating)

The two `UserProfileSettingsPage` navigation methods are **misleadingly named
relative to their URLs** (pre-existing code, not introduced by GAP-020):

| Method | Navigates to | Actually hosts |
|---|---|---|
| `navigate_to_profile()` | `/settings/personalization` | **Default Context Management** (toggle + Max Context Tokens + Preserve Recent Messages) |
| `navigate_to_personalization()` | `/settings/preferences` | **Theme toggle** (`PreferenceGeneral`) + **Voice Personalization** + **Sound Notifications** |

Don't "fix" the naming as a side-effect of any single case — `test_voice_configuration.py`
and `test_context_management.py` already depend on the current names. Just be aware
of the swap when picking which method to call.

## `/settings/preferences` page (Settings → PERSONAL → Preferences)

Renders (top to bottom, confirmed live): `PreferenceGeneral` (GENERAL accordion,
`defaultExpanded` — Theme toggle) → `VoicePersonalizationSection` (VOICE
PERSONALIZATION — voice/speed/volume/preview) → `SoundNotificationSection`
(SOUND NOTIFICATIONS).

### Theme toggle (`ThemeModeToggle.jsx`, single call site: `PreferenceGeneral.jsx`)

- **No testids as of 2026-07-24** (GAP-020 finding). Needed:
  `preferences-theme-dark-toggle` / `preferences-theme-light-toggle`, added via
  `buttonProps: {'data-testid': '...'}` on `themeArrayBtn` entries —
  `TabButtonItem.jsx` spreads `{...item.buttonProps}` onto the `ToggleButton`
  (confirmed, line 15). This is a single-use component (not shared), so
  hardcoding is correct — no `testId` prop indirection needed.
- **Selected state**: `.Mui-selected` class + `aria-pressed="true"/"false"` on
  the `<button>` — both are native MUI `ToggleButton` output, either is a valid
  state signal once the testid exists.
- **Exclusive-group no-op (important, easy to miss):** the group is
  `exclusive` (`TabGroupButton.jsx`) — clicking the **already-selected** button
  fires `onChange` with `newValue === null`, which the handler's guard
  (`if (newValue !== null)`) swallows entirely. No dispatch, no localStorage
  write, no repaint. Only clicking the **non-active** button produces a flip.
  Confirmed live both directions.
- **Persistence**: `localStorage['mode']` — values `'dark'`/`'light'`, **absent**
  (not pre-seeded `'dark'`) on a session that never touched it;
  `src/slices/settings.js:76`: `mode: localStorage.getItem('mode') || 'dark'`.
  `switchMode` reducer (line 109-111) always TOGGLES (`light`↔`dark`), ignoring
  which button's value was clicked — the click only matters for whether
  `newValue !== null` fires at all (see exclusive-group note above).
- **Palette signal — counter-intuitive, read before asserting colors.**
  `getComputedStyle(document.body).backgroundColor` (== `documentElement` ==
  `#root`, all three move together):
  - Dark → `"rgb(14, 19, 29)"` (`#0E131D`, theme's `gray60`, `src/darkPalette.js`)
    — an **explicit override**.
  - Light → `"rgba(0, 0, 0, 0)"` (transparent) — **no override at all**, the
    light look comes from the absence of a dark override revealing the default
    white canvas, NOT from a set "light" RGB value. Never assert a literal
    light color (`'white'`/`'#fff'`) — assert the dark↔transparent transition.
- **No network call** — pure client-side Redux + `localStorage.setItem`,
  confirmed via `get-network --status error` == `[]` across every switch.
- **Accordion container has no testid** (`PreferenceGeneral.jsx`'s
  `BasicAccordion` item passes no `testId`/`dataTestId` — confirmed via
  source read) — not needed unless a future case must disambiguate the
  General section from a sibling accordion; the Theme buttons are unique
  page-wide once testid'd.

### Voice Personalization / Sound Notifications sections

Already has partial page-object coverage (`UserProfileSettingsPage` — voice
dropdown via `#simple-select-Voice`, speed/volume sliders via
`input[aria-valuemin=...]`, `voice-personalization-section` /
`voice-preview-button` testids). These are **autosave** (network round-trip),
unlike Theme (synchronous, no network) — don't reuse
`wait_for_personalization_load()` as a Theme-only readiness wait; it couples on
the Voice dropdown's async TTS-voices fetch for no reason. Not otherwise
explored by GAP-020 — flagged here only so a future Theme-adjacent case
doesn't assume shared readiness semantics.

## `/settings/personalization` page (Default Context Management)

Out of scope for GAP-020 — not explored this run. Existing coverage:
`test_context_management.py` via `UserProfileSettingsPage.navigate_to_profile()`
+ `context-management-toggle` / `max-context-tokens-input` /
`preserve-recent-messages-input` testids (all pre-existing, confirmed present
in `user_profile_settings_page.py`).
