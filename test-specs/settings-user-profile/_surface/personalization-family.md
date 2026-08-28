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
