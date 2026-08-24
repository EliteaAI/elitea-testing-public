# Surface digest — settings-user-profile

Confirmed live on `localhost:5173` (`EliteaAI/EliteaUI` `automation/testids`,
DEV backend). Update as you verify/extend — this is a handle cache, not a
source of truth; re-verify a stale-looking entry against the live app before
trusting it.

## Routing — Settings sidebar

`/settings/` has two groups in the left nav:

**PROJECT**: General, AI Providers, Project Context, Secrets, Analytics, Usage
**PERSONAL**: Profile, Preferences, AI Personality, Memory, Personal Tokens,
Notifications

| Route | Page title | What lives there |
|---|---|---|
| `/settings/profile` | Settings: profile | Name / email / user ID / last login (read-only) |
| `/settings/preferences` | Settings: Preferences | Theme, Voice Personalization (voice/speed/volume/preview), Sound Notifications |
| `/settings/ai-personality` | Settings: ai-personality | Persona Management (default persona, user instructions) |
| `/settings/memory` | Settings: memory | **Context Management** (this is where "context management" / "token fields" TMS cases live — see below) |

**IMPORTANT — case-text trap (recurring):** several TMS cases (at least
ELITEA-2374, and per EliteaAI/elitea-testing-public#1129's body, this is a
known/recurring pattern) describe this area as "Personalization →
DEFAULT CONTEXT MANAGEMENT" or "user profile". That route
(`/settings/personalization`) **404s** — the section was relocated to
`/settings/memory` at some point and the case text / an existing page
object docstring (`user_profile_settings_page.py::navigate_to_profile()`)
were not updated. **Always navigate to `/settings/memory` for Context
Management / summarization cases**, regardless of what the case text says.
Clarification filed: EliteaAI/elitea-testing-public#1238.

## `/settings/memory` — Context Management accordion

Single accordion section, `data-testid="context-management-section"`,
expanded by default. Structure (`MemoryContextManagement.jsx` +
`MemorySummarization.jsx`):

```
Context Management [toggle: context-management-toggle]
  (only rendered when the toggle above is ON — conditional unmount, see below)
  ├─ Max Context Tokens [input: max-context-tokens-input]
  ├─ Preserve Recent Messages [input: preserve-recent-messages-input] — NEW 2026-08-06
  ├─ Context Editing [toggle: context-editing-toggle]
  └─ Automatic Summarization sub-section (MemorySummarization.jsx)
       ├─ Automatic Summarization [toggle: automatic-summarization-toggle] — NEW 2026-08-06
       ├─ Summarization instructions [textbox, no testid yet]
       └─ Target Summary Tokens [textbox, no testid yet]
```

**Disable mechanism is CONDITIONAL UNMOUNT, not `disabled`/grayed-out.**
`MemoryContextManagement.jsx` wraps everything below the top toggle in
`{isEnabled && (...)}`. Turning Context Management OFF removes the Max
Context Tokens field, Preserve Recent Messages field, Context Editing
toggle, AND the entire Automatic Summarization sub-section from the DOM —
they don't just gray out. Assert **absence** (`to_have_count(0)` /
`not_to_be_visible()`), not a `disabled` attribute. Toggling back ON
remounts everything with prior Formik values intact (confirmed: values
survive the hide/show round-trip).

Note: `Switch.BaseSwitch` for Automatic Summarization ALSO has its own
`disabled={!values.context_enabled}` prop in the JSX, but that's moot in
practice — the component unmounts before that prop ever matters, since it's
nested inside the same `{isEnabled && ...}` block one level up.

**Automatic Summarization's OWN toggle uses a DIFFERENT disable mechanism
than its parent (confirmed live, ELITEA-2377 session, 2026-08-06).** The
Automatic Summarization toggle disabling its own two children
(Summarization Instructions textarea, Target Summary Tokens input) is a real
`disabled` prop, NOT a conditional unmount — `MemorySummarization.jsx`:
`isSummarizationDisabled = !values.context_enabled || !values.enable_summarization`,
applied as `disabled={isSummarizationDisabled}` on both `Input.StyledInputEnhancer`
fields. Confirmed via live DOM inspection: clicking `automatic-summarization-toggle`
OFF leaves both fields present in the DOM with the HTML `disabled` attribute
set (`to_be_disabled()` is the correct assertion), unlike the parent
Context Management toggle's unmount (`to_have_count(0)`). Don't assume the
whole `/settings/memory` page uses one disable mechanism — it's per-toggle.

## Testids — provenance (as of this session)

| Testid | On `main`? | On `automation/testids`? |
|---|---|---|
| `context-management-section` | yes | yes |
| `context-management-toggle` | yes | yes |
| `max-context-tokens-input` | yes | yes |
| `context-editing-toggle` | yes | yes |
| `preserve-recent-messages-input` | **no** | yes — added ELITEA-2374 session, `EliteaAI/EliteaUI@b8155bda` |
| `automatic-summarization-toggle` | **no** | yes — added ELITEA-2374 session, `EliteaAI/EliteaUI@b8155bda` |
| `summarization-instructions-textarea` | **no** | yes — added ELITEA-2377 session, `EliteaAI/EliteaUI@be73caea` |
| `target-summary-tokens-input` | **no** | yes — added ELITEA-2377 session, `EliteaAI/EliteaUI@be73caea` (verified unique — a differently-scoped `context-modal-target-summary-tokens-input` exists in the unrelated chat-side Context Budget widget, `ContextStrategySummarization.jsx`) |

All testids referenced by cases through this session are now on
`automation/testids`; none yet on `main` (awaiting human promotion).

## Autosave

No Save button anywhere on `/settings/memory` or `/settings/preferences` —
everything autosaves. Confirmed via network capture:
- Toggle clicks (`context-management-toggle`, and presumably
  `context-editing-toggle`/`automatic-summarization-toggle`) fire
  `PUT /api/v2/social/author/` **immediately** → 200, followed by a
  refetch `GET /api/v2/social/author/`. Reliable — use as the wait signal.
- **Known bug (EliteaAI/elitea-testing-public#1129, OPEN):** typing into
  the numeric fields (Max Context Tokens / Preserve Recent Messages /
  Target Summary Tokens) does **not** autosave — the value shows on
  screen (React state) but no PUT ever fires, and it reverts on reload.
  Toggle-driven changes are unaffected. Don't be surprised if a
  typed-value test needs this soft-asserted against #1129.

## Test data gotcha

The shared `${TEST_USER}` account's Context Management values are NOT the
schema/fresh-account defaults — they carry whatever was last saved by
earlier manual or automated sessions (observed this session: Max Context
Tokens = `10000`, Preserve Recent Messages = `5`, Target Summary Tokens =
`4096`, Automatic Summarization = ON). Don't hard-assert a literal
"default" value in a new test; read-and-compare instead (see
`l3_context-management-toggle-enables-disables-fields_ELITEA-2374.md`
§ Blocked Steps for the worked example).

## Target Summary Tokens — min/max validation (ELITEA-2378 session, 2026-08-06)

Client-side Yup validation exists and is confirmed live. Source:
`VALIDATION_LIMITS.MAX_TOKENS = { MIN: 100, MAX: 4096 }`
(`EliteaUI/src/[fsd]/widgets/context-budget/lib/constants.js`), consumed by
`profileValidationSchema.summary_llm_settings.max_tokens` in
`src/[fsd]/features/settings/lib/helpers/profile.helpers.js` — the schema
that actually governs `/settings/memory` (NOT the sibling
`contextStrategyValidationSchema` in `context-budget/lib/validation.js`,
which is the chat-side Context Budget widget's own copy of the same limits —
don't confuse the two files, they duplicate the same `VALIDATION_LIMITS`
import but are wired to different Formik forms).

- Value below 100 (e.g. `99`) → input gets `aria-invalid="true"`, helper
  text "Target tokens must be at least 100". **No autosave PUT fires** —
  `useFormikAutoSaveOnBlur`'s `attemptSubmit()` runs `validateForm()` first
  and skips `submitForm()` when errors exist.
- Value above 4096 (e.g. `4097`) → `aria-invalid="true"`, helper text
  "Target tokens cannot exceed 4,096" (comma-formatted via
  `.toLocaleString()`). No autosave PUT.
- Value in range (e.g. `200`) → no error, autosave PUT fires and the
  response body echoes the new value:
  `default_summarization.target_summary_tokens`.
- The helper-text `<p>` carrying the error message has **no testid** —
  MUI's `FormHelperText`, rendered via `TextField`'s `helperText` prop in
  `MemorySummarization.jsx`. Assert the boundary via `aria-invalid` on the
  already-testid'd `target-summary-tokens-input` instead (state via a
  standard ARIA attribute, not a state-switched testid — compliant).
  Exact message text needs `testid needed: target-summary-tokens-error-text`
  (add via `FormHelperTextProps={{ 'data-testid': ... }}` on the
  `StyledInputEnhancer` — prop plumbing confirmed to exist in `InputBase.jsx`)
  if a future case wants to assert message text specifically.
- **Contradicts open bug #1129** ("numeric fields don't autosave when
  typed"): typing a VALID value (`200`) into Target Summary Tokens and
  blurring DID autosave successfully this session (PUT → 200, value
  echoed). Commented on #1129 with the evidence rather than closing it —
  may be field-specific (Max Context Tokens / Preserve Recent Messages
  untested this session) or a partial fix since filing. Don't assume #1129
  reproduces for Target Summary Tokens specifically without re-checking.

## Max Context Tokens — non-numeric/negative rejection (ELITEA-2391 session, 2026-08-06)

**Also contradicts #1129**: typing a valid value (`64000`) into Max Context
Tokens and blurring DID autosave successfully this session (PUT → 200,
value echoed as `default_context_management.max_context_tokens`). Same
caveat as Target Summary Tokens above — don't assume #1129 reproduces here
without re-checking; Preserve Recent Messages remains untested.

**The onChange handler filters keystrokes, not just validates on submit —
this is the actual mechanism behind "rejects non-numeric/negative".**
`handleConvertToNumberChange` (`src/[fsd]/widgets/context-budget/lib/validation.js:169-173`,
shared by BOTH Max Context Tokens and Target Summary Tokens — confirmed via
source, `MemoryContextManagement.jsx` and `MemorySummarization.jsx` both
call it) runs `value.replace(/[^0-9]/g, '')` on every keystroke before
`setFieldValue`. Consequences, confirmed live:
- Typing `"abc"` → every keystroke has zero digits → field ends up
  **empty**, not showing "abc". `aria-invalid="true"`, helper text "This
  field is required" (the field is `required` when `context_enabled` is
  true).
- Typing `"-100"` → the minus-sign keystroke is stripped identically to a
  letter → field ends up showing **`"100"`, not `"-100"`**. A literal
  negative number can **never** reach Formik state for either field — only
  its unsigned digits can. `100` then fails `min(1000)` →
  `aria-invalid="true"`, helper text "Max tokens must be at least 1,000".
  There is no distinct "negative rejected" error message anywhere in the
  schema; a typed negative always surfaces as a min-boundary error on
  whatever digits survive the strip.
- Neither invalid case fires an autosave PUT (same `validateForm()`-gates-
  `submitForm()` mechanism documented for Target Summary Tokens above).

Max Context Tokens' own limits: `VALIDATION_LIMITS.MAX_CONTEXT_TOKENS =
{ MIN: 1000, MAX: 10000000 }` (same constants file as `MAX_TOKENS`, i.e.
Target Summary Tokens' limits — don't confuse the two sibling constants).
Schema: `profileValidationSchema.max_context_tokens` in
`src/[fsd]/features/settings/lib/helpers/profile.helpers.js` — `.min(1000)`,
`.max(10000000)`, `.integer()`, `.required()` when `context_enabled: true`.

**Implication for automation**: a page-object setter that only accepts
`value: int` (e.g. the pre-existing `set_max_context_tokens()`) cannot
drive this test — it needs a sibling method that types a raw `str` and does
NOT bake in `wait_for_autosave()` (that method's docstring already flags it
as best-effort/non-committal about whether a PUT actually fired). Same
shape as `set_target_summary_tokens()`, added for ELITEA-2378.

## `/settings/profile` — Profile page + the ONLY Log out control (ELITEA-2252/2253/2254, 2026-08-24)

Confirmed live at both 1366×768 (the framework's headless viewport, `conftest.py:310`)
and 1728×861. Source: `src/[fsd]/features/settings/ui/profile/Profile.jsx`.

**Where logout lives — and where it does not.**
- The Log out button is a `BaseBtn` in the **content pane of `/settings/profile`**,
  the last control of the Profile card: `Profile.jsx:73-80`,
  `<BaseBtn variant="secondary" startIcon={<LogoutIcon/>} onClick={onLogout}>Log out</BaseBtn>`.
  Label is `Log out` **with a space**.
- **There is no Log out item in the Settings drawer.** PERSONAL ends at
  **Notifications** (`SettingsDrawer.jsx` renders only `SETTINGS_TABS_CONFIG` tabs).
  A whole-document text scan on `/settings/tokens` returned **0** `Log out` nodes.
- **There is no user/profile menu in the app-shell sidebar.**
  `src/[fsd]/widgets/sidebar-root/ui/button/UserButton.jsx` has a DotMenu with
  `Preferences` + `Logout`, but it is **dead code** — `grep -rn "UserButton" src/`
  finds no importer, and no `data-tour` user node renders live. Do not target it, do
  not add testids to it. This is the #1 thing that misleads a source read for
  "where is logout".
- ⇒ From any Settings sub-page, logging out costs **one drawer click** (→ Profile),
  then the button. This is why ELITEA-2254's "no extra navigation" premise fails.

**Geometry / scroll facts (asserted as relations, never as coordinates).**
- Log out is in-viewport with `window.scrollY == 0` at both viewports
  (1366×768 → `(525, 392) 112×28`; 1728×861 → `(706, 392)`).
- The settings **content pane is not scrollable** on this page
  (`scrollHeight == clientHeight`).
- The drawer **menu container is not scrollable** at 768px height
  (`617 == 617`) — so "visible without scrolling" holds for both panes.
- The icon is an inline `<svg width="16" height="16" viewBox="0 0 16 16"
  fill="currentColor">` in MUI's `startIcon` slot. Scope it off the button's testid;
  wiring a testid onto the icon itself would need a new DOM node (zero-functional-impact
  check forbids it).
- ⚠️ "Log out is the last focusable element in the pane" read `true` live but is **not**
  a safe assertion — `FieldWithCopy` rows can add copy affordances on hover.

**Clicking Log out is destructive and unobservable on localhost.**
`onLogout` dispatches redux `logout()` then sets
`window.location.href = origin + '/forward-auth/logout'` (`Profile.jsx:20-23`) — a hard
browser navigation to an **infrastructure** endpoint, not an in-app route. On localhost
that path is answered by the Vite SPA fallback (`curl … /forward-auth/logout` → **200**,
body = the SPA shell), so the app renders its global **"Page not found. Try Home page"**
view *inside the still-authenticated shell*, and a subsequent `/settings/profile` load is
**still logged in** (`Test Bot` / id 659 rendered, `document.cookie` empty throughout —
localhost auth is the `VITE_DEV_TOKEN` dev path, there is no Keycloak session and no
login page in existence locally).
⇒ **Never click Log out in a spec that shares a browser context.** It parks the context
outside the SPA routes. The only honest local observable of the click is
`expect(page).to_have_url(f"{BASE_URL}/forward-auth/logout")`.
The same `onLogout` shape is in the dead `UserButton.jsx:32`.

**Testids on this page — all `needs-adding` as of 2026-08-24**
(re-verified against `origin/main` and `origin/automation/testids` with `git fetch`):

| Testid | Where | Notes |
|---|---|---|
| `settings-profile-page` | `Profile.jsx` root `<Box sx={styles.container}>` | pure attribute add |
| `settings-profile-logout-button` | `Profile.jsx:73` `<BaseBtn>` | `BaseBtn` spreads `...restProps` onto `MuiButton` (`shared/ui/button/BaseBtn.jsx:31-40`), so `data-testid` passes straight to the `<button>` — no prop plumbing, no new node, no new hook |

Pre-existing and reusable: `personal-tokens-page-title` (**on `main` ✓ and
`automation/testids` ✓** — one of the few fully promoted handles in this area);
`sidebar-settings-button` (`automation/testids` only).
Still unadded anywhere as of this run: `settings-drawer`, `settings-content`,
`settings-nav-item-{tabId}` (requested by the ELITEA-2242/2243/2244 AFS too — whoever
lands first adds them).

**Console:** 0 errors across every load of `/settings/profile` and `/settings/tokens`
in this session, including the logout click. Neither the **#1771** (AI Personality
`disableUnderline`) nor the **#1203** (Secrets "Maximum update depth exceeded") filter
belongs on specs for this page — adding one would be masking.

**AFS files from this run:**
`l2_settings_profile_logout_button_visible_ELITEA-2252.md` (ready-for-automation),
`l1_settings_profile_logout_logs_user_out_ELITEA-2253.md` (**blocked** — env),
`l1_settings_logout_reachable_from_any_subpage_ELITEA-2254.md` (**blocked** — premise + env).
Drift consolidated onto clarification **#1772**.
