---
name: AI Providers page testid wiring
description: How testids were threaded through ai-providers accordion/select components (ELITEA-2392)
type: feedback
---

Surface: Settings → AI Providers (`/settings/ai-providers`,
`AIProvidersContent.jsx` → `ConfigurationsPanel.jsx` →
`ConfigurationSection.jsx` → `AIProviderAccordion.jsx` + `ConfigurationCard.jsx`).
Zero testids existed anywhere in this component tree before ELITEA-2392.

**`Select.SingleSelect`** (`src/[fsd]/shared/ui/select/SingleSelect.jsx`)
already accepts a `data-testid` prop (destructured as `'data-testid':
dataTestId`) — forwards it onto the underlying MUI `<Select>` AND adds a
`${dataTestId}-combobox` testid via `SelectDisplayProps`. No core-component
change needed; any caller can pass `data-testid="..."` directly. Used this to
wire `ai-providers-section-<slug>-default-selector` /
`...-high-tier-model-selector` / `...-low-tier-model-selector` by deriving the
value in `ConfigurationSection.jsx` from the already-threaded `sectionTestId`
prop (`` `${sectionTestId}-default-selector` ``) — no extra props threaded
through `ConfigurationsPanel.jsx` call sites needed for the selects.

**Section accordion header testid** lives on `AIProviderAccordion.jsx`'s
`StyledAccordionSummary` (the header button — `aria-expanded` attribute lives
here too, useful for an `expand_section()` helper that no-ops if already
expanded). It does NOT wrap the section's content (`StyledAccordionDetails`
is a DOM sibling, not a descendant of the header). Do NOT try to scope a
per-section card count by chaining `.locator()` off the header field via
xpath ancestor traversal — that trips the reviewer's mechanical
`.locator(`-without-`[data-testid=` grep even when the final selector is a
testid constant, because the ancestor-traversal call itself doesn't contain
`[data-testid=`. Instead: `ConfigurationCard.jsx`'s testid
(`ai-provider-configuration-card`) is a GLOBAL repeated-per-card value with
no section scoping element at all — isolate one section's cards via a
before/after count delta around `expand_section()`, not DOM ancestry.

Sections manage independent expand/collapse state (not a single-open
accordion) — expanding one never collapses another.

`ConfigurationCard`/`ConfigurationSection` return `null` (nothing in the DOM,
not an empty-state placeholder) when a section has zero configured items —
confirmed for Vector Storage + AI Credentials on the shared `${TEST_USER}`
project (`Private`/399). Distinguish "correctly hidden" from "silently
broke" via the API response body (per-section `models` call has a clean
`items: []`), not DOM absence alone — the combined `configurations` call
(drives AI Credentials) reclassifies raw `section=credentials` items into
`ai_credentials` client-side by `type` (see
`src/hooks/useMultiSectionConfigurations.js` `AI_CREDENTIAL_TYPES`), so there
is no direct "ai_credentials-only" response to parse; a 200 status on the
combined call plus DOM absence is the practical evidence ceiling there.

Testid commits: `EliteaAI/EliteaUI@5119ba70` (page title, 7 section headers,
config card), `EliteaAI/EliteaUI@ff547e50` (selects).
