---
name: Generate Agent Suggested Resources quirks (implementer)
description: SuggestionItem.jsx's entityType-conditional secondaryText (item.type for toolkit, item.description otherwise), ResourceSuggestions.jsx's empty-array-returns-null section behavior, and the mock-the-generate-draft-response-over-new-fixture technique for exercising multi-category suggestion coverage read-only
type: feedback
---

## Context

From ELITEA-1907 (`GenerateAgentReviewForm.jsx`'s Suggested Resources section
— `ResourceSuggestions.jsx` / `SuggestionItem.jsx`, agent "Build with AI"
review form). Both components had **zero** `data-testid` prior to this case;
added via `add-data-testid`:

- `generate-agent-resource-section-{entityType}` / `-section-title-{entityType}`
  on the per-category container (`ResourceSuggestions.jsx`)
- `generate-agent-resource-item-{entityType}-{id}` / `-checkbox-` / `-name-` /
  `-description-` on each suggestion card (`SuggestionItem.jsx`)

## Quirk 1 — secondaryText is entityType-conditional, not always "description"

`SuggestionItem.jsx:20`:
```js
const secondaryText = entityType === 'toolkit' ? item.type : item.description;
const showSecondary = secondaryText && secondaryText !== item.name;
```

For `entityType === "toolkit"` suggestions, the card's secondary-text element
(testid `generate-agent-resource-description-toolkit-{id}` — same element
name as every other category) renders **`item.type`** (the toolkit's
technical type, e.g. `"github"`), **NOT `item.description`**. Every other
entity type (`mcp`, `pipeline`, `agent`, `skill`) renders `item.description`
as you'd expect from the testid name.

**Implication for tests:** if you're asserting the "description" testid
against a toolkit suggestion, assert `item.type`'s value, not
`item.description`'s. A test that sets a toolkit's `description` field in a
mocked/seeded suggestion and expects it to show up will fail — silently
looking like a broken feature when it's actually a deliberate design (toolkit
cards disambiguate by integration type, not free text). This is a
reverse-masking-guard case: the case text ("shows name and description") is
stale for the toolkit category specifically; assert the live per-entityType
contract instead of the literal wording.

## Quirk 2 — empty category renders no section, not an empty one

`ResourceSuggestions.jsx:10`: `if (!items?.length) return null;` — a category
with zero suggestions renders **nothing at all**, not a section with a
"no suggestions" placeholder. Write category-count-aware assertions
(`is_resource_section_visible(entity_type)` checking element *count*, not
just visibility) rather than assuming all 5 titled sections (`Suggested
Toolkits:`, `Suggested MCP:`, `Suggested Pipelines:`, `Suggested Agents:`,
`Suggested Skills:`) always render.

## Technique — mock the generate-draft response instead of a new fixture

The live project's `generate_application_draft` response is data-dependent
on project inventory (which Toolkits/Agents/Pipelines/MCPs exist and match
the prompt). In this project (id 399) only one MCP (`Remote Github`, id 3,
**empty description**) was live-suggestible for a GitHub/Jira prompt —
insufficient to demonstrate multi-category coverage or the
"description present" rendering path.

Rather than provisioning a new Toolkit/MCP fixture (create + teardown, shared-
state risk), reuse the modal's existing `mock_generate_success(draft_payload)`
method (already built for ELITEA-1915's failure/retry tests, on
`GenerateEntityModalPageBase`) with a **synthetic multi-category payload**:
Toolkit + Pipeline with non-empty descriptions, MCP mirroring the live
id-3/null-description shape exactly, Agents/Skills empty. This is
read-only-by-default (Hard Rule 10) — zero fixture create/teardown/leak-risk
— and it exercises MORE of the case's scope (multiple populated categories +
both description-present/absent rendering paths + the empty-category-no-
section path) than the live environment alone could ever demonstrate.
Applies to any future "Build with AI" suggestion-rendering case (Skill's
equivalent flow, if/when it grows suggestions) — mock the draft response
first; only reach for a real fixture if the assertion genuinely needs a live
round-trip (e.g. testing the suggestion *ranking*/relevance algorithm itself,
not just how the review form renders whatever it's given).
