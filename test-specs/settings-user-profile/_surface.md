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
