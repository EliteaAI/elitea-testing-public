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

## ELITEA-2397 additions (LLM tier mutation flow)

- The `-combobox` suffix `SelectDisplayProps` auto-derives is the actual
  clickable/readable node — a plain `expect(outer_field).to_be_visible()`
  works on the outer testid, but reading the SELECTED text or clicking to
  open the dropdown must go through the `-combobox` suffixed field, not the
  outer one.
- `ConfigurationCard.jsx`'s `statusText` Typography renders `displayName` +
  `statusText` + any tier-badge Typography as SIBLING children with **no
  whitespace separator** in the concatenated `textContent`
  (`"GPT-5.4OK • Shared"`, `"GPT-5.4OK • Shared High-Tier"`). An anchored
  `^name$` regex `.filter(has_text=...)` on the outer
  `ai-provider-configuration-card` testid therefore NEVER matches — confirmed
  live, this is what timed out the first test run. Fix: added a dedicated
  `ai-provider-configuration-card-name` testid on the `displayName`
  Typography alone (`EliteaAI/EliteaUI@e1ea650c`), then scope the outer card
  via `.filter(has=<name-locator>)` (`AIProvidersPage.card_for_model()`).
  Generalizes: any card/row component that concatenates multiple dynamic text
  fields into one Typography sibling group needs its OWN name-only testid for
  exact-match identification — the outer container testid alone is only good
  for substring/count checks.
- Tier badge testid `ai-provider-configuration-badge`
  (`EliteaAI/EliteaUI@4213b6c8`) is on THREE separate JSX nodes
  (`isDefault`/`isHighTier`/`isLowTier`, independently-conditional booleans,
  not a ternary on one element) — canon ruling #277 (same-element
  conditional pair) does not apply; this is just the same static-repeated-
  value pattern as the card testid itself.
- The `POST /configurations/models/{project_id}` save call's body is
  `{name, target_project_id, section}` where `section` is `"llm"` (Default) /
  `"llm_high_tier"` / `"llm_low_tier"` — confirmed via
  `EliteaUI/src/api/configurations.js`'s `setProjectDefaultModel` mutation +
  `ConfigurationsPanel.jsx`'s `onChangeDefaultModel(...)` call sites. No
  nullable/clear payload shape exists anywhere in that file — a tier that
  starts UNSET (no value) cannot be programmatically cleared via this
  endpoint, and the MUI dropdown itself offers no blank option either. A test
  that must restore an originally-unset tier has no UI-only or documented
  API-only path back to "unset" as of 2026-08-06.
- Every tier's CURRENT value + the full candidate option list is derivable
  from the `section=llm` GET response body alone (`default_model_name`/
  `high_tier_default_model_name`/`low_tier_default_model_name` +
  `*_project_id` counterparts at the top level; each `items[]` entry carries
  `name`/`project_id`/`display_name`/`high_tier`/`low_tier`) — no need to
  read the DOM/hidden textbox to construct a `select-option-{name}<<>>
  {project_id}` testid target.
