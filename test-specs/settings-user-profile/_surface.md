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

---

## Index — this digest is split (2026-08-28, settings-w08)

It outgrew a comfortable single read (~450 lines). This file stays the entry point every
AFS links to; the detail lives in `_surface/`. **Read the file that covers what you are
touching**, not all three.

| File | Covers |
|---|---|
| [`_surface/memory-context-management.md`](_surface/memory-context-management.md) | `/settings/memory` — Context Management + Automatic Summarization accordion, its testids + provenance, the conditional-unmount disable mechanism, autosave (incl. the #1129 numeric-field bug), test-data gotchas, Target Summary Tokens & Max Context Tokens validation limits |
| [`_surface/profile-and-drawer.md`](_surface/profile-and-drawer.md) | `/settings/profile` — the ONLY Log out control, its geometry/scroll facts, the dead `UserButton.jsx`, plus the Settings-drawer testids added during ELITEA-2252 and the reusable facts (svgr prop spread, `BaseBtn` prop spread, `data-active` stringification, two `<main>` elements, HMR lag) |
| [`_surface/personalization-family.md`](_surface/personalization-family.md) | **The "Personalization page" does not exist** — where each of its sections really lives; `BasicAccordion`'s two testid shapes; accordion collapse = `visibility: hidden` (not unmount); `/settings/preferences`, `/settings/ai-personality` and `/settings/profile` avatar inventories; the per-route console-error map |

### Quick pointers (the traps that cost the most time here)

- **`/settings/personalization` 404s.** Context Management is `/settings/memory`; the other
  "Personalization" sections are `/settings/preferences`; "Default Personality" is
  `/settings/ai-personality`. Clarifications: #1238, #1772, #1960.
- **Two different hide mechanisms on one surface:** a collapsed *accordion* keeps children
  mounted and hides them via `visibility: hidden` (`not_to_be_visible()`); the Context
  Management *toggle* conditionally unmounts them (`to_have_count(0)`).
- **Known console error #1771** (`disableUnderline`) fires on `/settings/memory` and
  `/settings/ai-personality`, never on `/settings/profile`.
- **Shared mutable account state:** `persona` and the Context Management values belong to the
  shared `${TEST_USER}` record — read-before-write, restore in teardown, never hardcode a
  "default".
