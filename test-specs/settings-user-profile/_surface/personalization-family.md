## The "Personalization page" does not exist — where its pieces actually live (settings-w08, 2026-08-28)

Confirmed live this session (qa-engineer analyst, cluster ELITEA-2371/2372/2373/2380/2387).
This **supersedes nothing** in the `/settings/memory` sections above; it generalises the
`#1238` trap from one case to the whole family. Clarification for this cluster:
**EliteaAI/elitea-testing-public#1960** (siblings: #1238, #1772 — cross-linked, don't re-file).

`GET /settings/personalization` → the app's global **"Page not found. Try Home page"** view
(no Settings drawer, no `settings-content`). The five accordion sections a whole family of
TMS cases attributes to that one page are distributed like this:

| Case's section | Live route | Live accordion title |
|---|---|---|
| profile area (avatar / name / email) | `/settings/profile` | not an accordion — `UserAvatar` + `FieldWithCopy` rows |
| `GENERAL` | `/settings/preferences` | `GENERAL` (Theme only) |
| `DEFAULT CONTEXT MANAGEMENT` (+ `DEFAULT SUMMARIZATION`) | `/settings/memory` | `CONTEXT MANAGEMENT` / `Automatic Summarization` |
| `LONG-TERM MEMORY` | **nowhere** | dead code — see below |
| `VOICE PERSONALIZATION` | `/settings/preferences` | `VOICE PERSONALIZATION` (`voice-personalization-section`) |
| `SOUND NOTIFICATIONS` | `/settings/preferences` | `SOUND NOTIFICATIONS` |
| "Default Personality" | `/settings/ai-personality` | `PERSONA MANAGEMENT` → `Default persona` select |

**`LONG-TERM MEMORY` is dead code.** `MemoryLongTermMemory.jsx` exists (and carries the exact
copy *"Coming soon - Manage what the AI remembers about you across conversations"*), but its
only import is commented out at `MemoryContextManagement.jsx:13`; `grep -rn
"MemoryLongTermMemory" src/` finds no live importer. Live DOM on `/settings/memory` and
`/settings/preferences`: no `Long-term`, no `Coming soon`.

## `BasicAccordion` — the two testid shapes it already supports (no new DOM node needed)

`src/[fsd]/shared/ui/accordion/BasicAccordion.jsx`:
- `data-testid` prop → the wrapper `<Box>` (line 40 destructure, line 45 apply). This is what
  `context-management-section` / `voice-personalization-section` are.
- **per-item `testId`** → straight onto the `StyledAccordionSummary` (line 70), i.e. the
  **clickable header** that carries `aria-expanded`. This is the handle to add for any
  collapse/expand case — pure prop plumbing, zero-functional-impact clean.
- `defaultExpanded` defaults to **`true`** (line 35), so a section that doesn't pass the prop
  (e.g. `SoundNotificationSection`) is still expanded on load. Verified live: all three
  Preferences accordions + `CONTEXT MANAGEMENT` read `aria-expanded="true"` on load.
- ⚠️ `aria-controls` is `panel-content-${index}` **per item**, and every section here is a
  one-item accordion ⇒ **all of them share `aria-controls="panel-content-0"`**. Never key a
  locator on it.

## Accordion collapse: `visibility: hidden`, NOT unmount (verified live)

Collapsing a section leaves its children **in the DOM**:
`[data-testid="max-context-tokens-input"]` still returns count **1** while `CONTEXT
MANAGEMENT` is collapsed. What changes is the `MuiCollapse-root`: class `MuiCollapse-hidden`,
`height: 0px`, **`visibility: hidden`** — so `element.checkVisibility()` is `false` and
Playwright's `not_to_be_visible()` is the correct assertion.
**`to_have_count(0)` is wrong here.** That shape belongs to the *other* mechanism on this
surface — `context-management-toggle`'s conditional unmount (documented above). One page,
two different hide mechanisms; pick per control, not per page.

## `/settings/preferences` — inventory (2026-08-28)

Header `Preferences`. Three accordions in DOM order: `GENERAL` (Theme toggle),
`VOICE PERSONALIZATION` (`voice-personalization-section`; Voice / Speed / Volume /
`voice-preview-button`), `SOUND NOTIFICATIONS`. **No Save button.** Only testid present:
`voice-personalization-section` + `voice-preview-button`. Needs adding for collapse/expand
work: `preferences-general-section(-header)`, `voice-personalization-section-header`,
`sound-notifications-section(-header)`, `context-management-section-header`.

## `/settings/ai-personality` — Persona Management (2026-08-28)

Header `AI Personality`, one accordion `PERSONA MANAGEMENT`, expanded by default. Controls:
`Default persona` (`SingleSelect`) + `User instructions` (multiline, hidden when persona is
`none`). **No Save button.**

- Options (`PERSONA_OPTIONS`, `src/common/constants.js:1120`): Generic / **QA** / Nerdy /
  Quirky / Cynical / None / Bare. Each `<li role="option">` already carries the shared
  generic testid **`select-option-{value}`** (`SingleSelect.jsx:416`) — dynamic pattern, so a
  class constant `'[data-testid="select-option-{}"]'`, never an inline f-string.
- `SingleSelect` accepts `data-testid` and additionally emits `${dataTestId}-combobox` on the
  display element (`SingleSelect.jsx:82,661-662`) — pure prop pass-through.
- **Autosave**: picking an option fires `PUT /api/v2/social/author/` → **200** immediately,
  then a refetch `GET`. Verified persisted across navigate-away/back **and a full reload**.
  `UserProfileSettingsPage.wait_for_autosave()` (line 489) is the reusable wait.
- `User instructions` placeholder is **per persona**
  (`No custom instructions for the QA persona yet…`) — a cheap secondary signal that a
  persona change reached Formik state.
- ⚠️ **Render race**: right after navigating to this route the select is briefly absent from
  the DOM (an immediate probe returned `null`, the next returned the value). Wait on the
  select, never a sleep.
- ⚠️ **Shared mutable state**: `persona` lives on the shared `${TEST_USER}` account and also
  drives chat behaviour. Read-before-write and restore in teardown. Observed value at the
  start of this session: `Generic` (restored to `Generic` at the end).

## `/settings/profile` — the avatar is usually INITIALS, not an image (2026-08-28)

`UserAvatar` (`src/components/UserAvatar.jsx`) renders an `<img>` **only when
`state.user.avatar` is set**. The shared test user (`Test Bot`, id 659) has none, so the live
render is the MUI `Avatar` initials fallback — text `TB`, **zero `<img>` nodes** inside
`settings-profile-page`. Any "avatar image is shown" assertion must accept both branches.
`UserAvatar` already accepts a `testId` prop and applies it in **both** branches (lines 20, 38).

`FieldWithCopy` (`features/settings/ui/ai-providers/FieldWithCopy.jsx`) has **no testid
plumbing** — it needs a `testId` prop added and named at the **call site** (it is reused by AI
Providers, so never hardcode a profile-scoped testid inside it). Its value `<Typography>` has
an `onClick` copy handler + toast — read text, don't click.

Live values this session: name `Test Bot` (rendered twice — under the avatar and as
`Full name:`), `Email: testbot@elitea.ai` (== `settings.test_user_email` from `.env.test`,
verified equal — so config is a valid external oracle for the email), `User ID: 659`.
**Console: 0 errors on `/settings/profile`** — do NOT add the #1771 filter to specs for this
route; it would be masking.

## Console-error map for this surface (2026-08-28)

| Route | Errors on load |
|---|---|
| `/settings/profile` | none |
| `/settings/preferences` | none observed |
| `/settings/memory` | **1** — the known **#1771** React `disableUnderline` warning, via `MemorySummarization.jsx`'s `StyledInputEnhancer` |
| `/settings/ai-personality` | **1** — same #1771 message, via `AIPersonalityPersonalization`'s `StyledInputEnhancer` |

A "no console errors" step on `/settings/memory` or `/settings/ai-personality` must filter
exactly that message (linked known defect), nothing broader.

## Resolved/added during ELITEA-2372/2373/2387 implementation (2026-08-29, test-automation-engineer)

**Testids added on `automation/testids`** — all pure attribute/prop adds, no new DOM node,
no new hook (EliteaAI/EliteaUI@fa505e37, plus EliteaAI/EliteaUI@36733706 for the avatar image):

| Testid | Where | Shape |
|---|---|---|
| `preferences-general-section` / `-header` / `preferences-general-content` | `PreferenceGeneral.jsx` | `BasicAccordion` `data-testid` + item `testId` + attribute on the existing content `<Box>` |
| `sound-notifications-section` / `-header` | `SoundNotificationSection.jsx` | same two `BasicAccordion` props |
| `sound-notifications-content` | `SoundNotificationControls.jsx` root `<Box>` | feature-local component, single consumer |
| `voice-personalization-section-header` | `VoicePersonalizationSection.jsx` | item `testId` (the wrapper already had one) |
| `context-management-section-header` | `MemoryContextManagement.jsx` | item `testId` |
| `settings-profile-avatar` (+ `-image`) | `Profile.jsx` / `UserAvatar.jsx` | `testId` prop; the `-image` value is DERIVED inside `UserAvatar` via MUI's `imgProps` slot |
| `settings-profile-display-name` | `Profile.jsx` | attribute |
| `settings-profile-fullname-value`, `settings-profile-email-value` | `Profile.jsx` call sites | new caller-supplied `testId` prop on `FieldWithCopy` |
| `ai-personality-persona-section`, `ai-personality-persona-select` (+ auto `-combobox`), `ai-personality-user-instructions-textarea` | `AIPersonalityPersonalization.jsx` | `BasicAccordion`/`SingleSelect` props + the established `inputProps={{ 'data-testid': … }}` |

**Facts worth reusing**

- **`UserAvatar`'s image branch is now addressable without a raw `img` hop.** MUI `Avatar`
  accepts `imgProps`, so `UserAvatar` emits `${testId}-image` on the `<img>` whenever the
  caller passes a `testId` — the same derive-from-the-caller shape `SingleSelect` uses for
  `-combobox`. Count of that testid IS the branch discriminator (1 = image, 0 = initials).
  This is NOT a #579 case; do not reach for a scoped raw handle here.
- **A collapse probe on CONTEXT MANAGEMENT must be `context-management-toggle`, not
  `max-context-tokens-input`.** The numeric fields are conditionally unmounted when the
  toggle is off (shared mutable account state), so they read 0 elements for a reason that
  has nothing to do with the accordion. The toggle is the always-mounted child.
- **`page.expect_response` beats `UserProfileSettingsPage.wait_for_autosave()` for the
  persona PUT.** That helper is a `networkidle` wait with a `wait_for_timeout` fallback: it
  cannot identify the request or read its status, and `networkidle` is a documented flake
  source on this app (#1847 — the Socket.IO polling transport never goes quiet). Wrapping
  the interaction in `page.expect_response(<PUT /api/v2/social/author/>)` and asserting
  `status == 200` is strictly stronger and still sleep-free. Restore in a `finally`, waiting
  for the restore's own PUT.
- ⚠️ **The Vite dev server does NOT reliably see edits on this OneDrive-backed checkout.**
  Three specs failed their first run with "element(s) not found" on brand-new testids while
  the JSX on disk was correct and committed; `curl http://localhost:5173/src/<path>.jsx`
  showed the server still serving the pre-edit transform, and `touch`-ing the files did not
  wake the watcher. **Restarting `npm run dev` fixed it, and the same three specs went 3/3
  green.** Before suspecting a testid, `curl` the module off the dev server and grep it —
  that is a 2-second check that distinguishes a stale watcher from a real locator bug (this
  is the sharper form of the "HMR lag" note in `_surface/profile-and-drawer.md`: the fix is
  a server restart, not a re-run).

## `/settings/ai-personality` — deeper inventory (settings-w08 cluster ELITEA-2381/2382/2383/2384, 2026-08-29)

Confirmed live this session (qa-engineer analyst). Extends the `/settings/ai-personality`
section above; nothing there is superseded.

### The persona option list — exactly SEVEN, and the count is part of the contract

`Default persona` renders 7 `li[role="option"]` rows, DOM order below. Source of truth
`PERSONA_OPTIONS`, `src/common/constants.js:1120-1132`. Several TMS cases say "six" —
that is case-text drift (clarification **#1963**), not a product bug.

| # | testid | value | Label | Description |
|---|---|---|---|---|
| 1 | `select-option-generic` | `generic` | Generic | Balanced, professional assistant |
| 2 | `select-option-qa` | `qa` | QA | Precise, technical, testing-focused |
| 3 | `select-option-nerdy` | `nerdy` | Nerdy | Technical deep-dives, detailed explanations |
| 4 | `select-option-quirky` | `quirky` | Quirky | Creative, playful, thinking outside the box |
| 5 | `select-option-cynical` | `cynical` | Cynical | Skeptical, challenges assumptions |
| 6 | `select-option-none` | `none` | None | No personality overlay applied |
| 7 | `select-option-bare` | `bare` | Bare | No Elitea identity — only your instructions plus tool-required guidance |

The currently-selected row carries `aria-selected="true"`. For a count/order assertion use
an attribute-prefix class constant (`'[data-testid^="select-option-"]'`) — still a literal
`[data-testid=` selector, so the mechanical grep passes. Never `li[role="option"]`.

### `User instructions` is a PER-PERSONA map, not one global field

`AIPersonalityPersonalization.jsx` writes `personality_instructions.<persona>`; the textarea
renders only the slot of the currently selected persona, and the whole field is **absent
from the DOM when the persona is `none`** (`values.persona !== 'none'` guard). Server shape:

```json
"personality_instructions": {"bare":"","cynical":"","generic":"","nerdy":"…","none":"","qa":"","quirky":""}
```

⇒ **any spec that types here must pin the persona first and read back under the same
persona**, and teardown must restore BOTH the persona and the slot's text. Verified live:
text saved under `Nerdy` read back empty after switching to `Quirky`, and reappeared on
switching back.

### Two different autosave triggers in ONE accordion

- **Persona select — saves on SELECTION.** `handlePersonaChange` calls `onAutoSaveRequested`
  directly, so `PUT /api/v2/social/author/` → 200 fires immediately; no outside click needed.
  A case step saying "click outside to trigger autosave" for this control is a harmless no-op.
- **User instructions textarea — saves on BLUR.** `handleInstructionsChange` only calls
  `setFieldValue`; the write comes from `AIPersonalityFormContent`'s
  `useFormikAutoSaveOnBlur` wrapper. Blur really is the trigger here.

⚠️ **Do not blur onto the accordion header** — clicking `Persona Management` collapses the
section (`aria-expanded` → `false`, confirmed live). Pick a neutral node inside
`settings-content`.

### ONE `PUT /api/v2/social/author/` carries BOTH structures

The author payload holds `personalization.{persona,personality_instructions,…}` **and**
`default_context_management.{enabled,max_context_tokens,preserve_recent_messages}` **and**
`default_summarization.*`. Verified live: saving a persona while the context-management
toggle was OFF returned 200 and left `default_context_management.enabled: false` intact.
That shared payload is the real independence risk ELITEA-2383 points at — and the reason a
personality spec's teardown can silently clobber a context-management spec's baseline.

### `context-management-toggle`: the testid is on the SwitchBase `<span>`, not the input

`document.querySelector('[data-testid="context-management-toggle"]').tagName === "SPAN"`
(`MuiSwitch-switchBase`). Read `checked` from the `<input type="checkbox">` **inside** it.
Playwright's `.check()`/`.is_checked()` on the span will not do what you expect.

### A conversation SNAPSHOTS the persona at creation — `meta.persona`

There is **no per-conversation personality indicator in the UI** (`meta.context_strategy` is
the only conversation meta the front end consumes). The record carries it though, on both
endpoints the normal user path already hits:

- `POST /api/v2/elitea_core/conversations/prompt_lib/<project>` → **201**, on sending the
  first message
- `GET /api/v2/elitea_core/conversation/prompt_lib/<project>/<id>` → **200**, on opening one

Both return `meta.persona` plus a **top-level `instructions`** string already resolved from
that persona's slot. Verified live: conv `9871` created under `Quirky` → `"quirky"` / `""`;
default then moved to `Nerdy` (slot held text); re-opening `9871` still read `"quirky"` /
`""`; conv `9872` created after → `"nerdy"` / the marker text. **This is the deterministic
observable for any "settings apply to new conversations only" case involving personality** —
no LLM-tone judgment required. The 201 lands before the model answers, so such a spec never
waits on an AI response.

⚠️ **`chat-send-button` is pointer-intercepted on the fresh `/chat` view** — a click times
out with `<div class="MuiBox-root css-15msj7j"> … intercepts pointer events`. Send with
**Enter** (`ChatPage.send_message(text, use_enter=True)`).

ℹ️ The project's conversation list still renders **folders only, zero
`chat-conversation-item-*` rows** (unchanged since ELITEA-2390) — no "existing conversation"
can be assumed; a spec must create its own.

### Console-error map — unchanged, re-confirmed

`/settings/ai-personality` logs exactly **one** error per load, the known **#1771**
`disableUnderline` React warning. `/settings/memory` the same. `/settings/profile` none.
Filter by that exact fragment; anything broader is masking.
