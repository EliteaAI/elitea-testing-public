---
name: Settings Memory context management route and unmount behavior
description: /settings/personalization 404s; Context Management lives at /settings/memory and hides (unmounts) its fields on toggle-off, not grays them out
type: project
---

Confirmed live 2026-08-06 (ELITEA-2374, `EliteaAI/elitea-testing-public` batch
`elitea-2374-context-mgmt-toggle`), `localhost:5173` / `automation/testids` / DEV backend.

**Route drift (recurring — multiple TMS cases share this mistake):** cases in
the `settings-user-profile` module describe navigating to "Personalization →
DEFAULT CONTEXT MANAGEMENT" or similar. That route
(`/settings/personalization`) **404s**. The real location is
**Settings → Memory (`/settings/memory`)**, accordion section titled plain
"Context Management" (no "DEFAULT" prefix). The page object
`automation/pages/user_profile_settings_page.py::navigate_to_profile()`
docstring already half-documents this ("/user-settings/profile is not a
valid route... served at /settings/personalization") but THAT route is
*also* stale now — it 404s too. Always verify live before trusting either
the case text or the page object docstring for this area. Clarification
filed: EliteaAI/elitea-testing-public#1238. Related pre-existing bug that
independently confirms the relocation: EliteaAI/elitea-testing-public#1129.

**Disable mechanism is conditional unmount, not disabled/grayed:**
`MemoryContextManagement.jsx` wraps Max Context Tokens / Preserve Recent
Messages / Context Editing toggle / the whole `MemorySummarization`
sub-section in `{isEnabled && (...)}`. Turning the Context Management
toggle OFF removes all of them from the DOM entirely — assert absence
(`to_have_count(0)` / `not_to_be_visible()`), never a `disabled` attribute
check, for any case describing these fields as "grayed out" when the
parent toggle is off. Toggling back ON remounts with prior Formik values
intact (values survive the hide/show round-trip — confirmed).

**Test data gotcha:** the shared `${TEST_USER}` account's values here
(Max Context Tokens, Preserve Recent Messages, Target Summary Tokens,
Automatic Summarization checked-state) are NOT fresh-account defaults —
they're whatever a prior session last saved. Don't hard-assert a literal
case-stated "default" (e.g. case ELITEA-2374 says 64000, live account
showed 10000) — read-and-compare against the value captured at test
start instead.

**Autosave:** no Save button; every toggle click fires
`PUT /api/v2/social/author/` → 200 immediately (reliable wait signal).
Typing into the numeric fields does NOT autosave — that's a separate,
already-filed, OPEN bug (EliteaAI/elitea-testing-public#1129) unrelated to
toggle-only cases.

**Chat-side effect of the global toggle (confirmed live 2026-08-19, ELITEA-2216,
`chat-remaining-w15` batch):** with the toggle OFF, the chat Context Budget widget
(collapsed `0%` indicator, expanded panel, AND the "Edit context settings" modal
opened via `context-budget-edit-button`) all read literal `0` for
tokens/percentage/Messages/Summaries — even after a real, complete AI exchange.
No context-management-specific network call fires at all while disabled (backend
doesn't compute/track usage when off, not merely hiding a computed value). The
Context Budget panel's collapsed-by-default-behind-Participants-panel timing
(`ChatPage.expand_participants_panel()` needed) is identical whether the setting
is ON or OFF — not a disabled-state quirk. Full AFS:
`test-specs/chat-interface/l3_context-management-disabled-widget-stays-zero_ELITEA-2216.md`.

Full surface digest: `test-specs/settings-user-profile/_surface.md`.
