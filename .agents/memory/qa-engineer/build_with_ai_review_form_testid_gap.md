---
name: Build with AI review-form testid gap
description: Shared GenerateEntityModal shell getting testid-wired for an entity does not cover that entity's own review-form child component; audit review-form fields separately. Raw fetch() DELETE from page JS context CORS-fails on this app.
type: feedback
---

## Pattern: shell testids ≠ review-form testids

The "Build with AI" flow (`GenerateEntityModal.jsx`/`GenerateEntityButton.jsx`)
is a shared presentation shell used by Agent, Skill, (and likely future)
entities. Each entity wraps it (`GenerateAgentModal.jsx`/`GenerateSkillModal.jsx`)
and supplies its own `render Review` callback pointing at an entity-specific
review-form component (`GenerateAgentReviewForm`/`GenerateSkillReviewForm`).

Observed across three related cases:
- ELITEA-1915 (Agent): found the *entire* shell had zero testids at the time.
- ELITEA-2001 (Skill): found the Skill wrapper never wired the shell's
  `*TestId` props at all (Agent wrapper had already been fixed post-1915),
  and explicitly scoped the Skill review-form's own fields (Name/Description/
  Instructions) as out-of-scope/future-gap.
- ELITEA-1990 (Skill, this entry's origin): confirmed the shell + wrapper
  testids now exist for Skill (`generate-skill-*`), but the review-form's
  own three `TextField`s (in `GenerateSkillReviewForm.jsx`, a *separate*
  child component from the shell) had ZERO testids — a distinct gap the
  shell fix never touched. Added
  `generate-skill-review-{name,description,instructions}-input` via
  `slotProps.htmlInput['data-testid']` on the native input (same pattern as
  `generate-skill-prompt-input`).

**Lesson:** when auditing a "Build with AI"-style case, check the shell,
the wrapper's prop-passing, AND the entity-specific review-form child as
three independent testid surfaces — a fix to one doesn't imply the others
are covered. If a future Agent-side "review fields editable" case shows up
(mirroring this ELITEA-1990 pattern), check `GenerateAgentReviewForm.jsx`
for the same gap before assuming Agent is already fully wired.

## Cleanup gotcha: raw fetch() DELETE fails cross-origin

Attempting `fetch('/api/v2/.../skill/{id}', {method:'DELETE'})` directly
from the page's own JS context (via Playwright's `browser_evaluate`/CDP
`evaluate`) fails with a CORS error on this app — the request gets
redirected through `dev.elitea.ai/forward-auth/auth_oidc/login` (missing
`Access-Control-Allow-Origin` on that redirect target), even though GETs
issued the same way during normal page load succeed fine. This is because
the real app never makes a bare unauthenticated `fetch()` this way — it
uses its own configured HTTP client (axios + proper headers) which this
ad-hoc console approach doesn't replicate.

**Use instead, for exploration/analyst cleanup:**
1. The UI's own delete flow (e.g. Skill: `skill-controls-menu-button` →
   `skill-delete-menu-item` → type-to-confirm dialog → `Delete`) — reliable,
   already proven.
2. For automated test teardown: the project's existing cookie-authed API
   client (e.g. `SkillAPI.delete_skill()`, `automation/api/client.py`) —
   correct auth, no CORS issue since it's a real HTTP client, not a
   same-origin browser `fetch()`.

Never use a bare page-context `fetch()` DELETE as a cleanup shortcut on
this app — it will silently fail with a CORS error, not a clean 200/204.
Also true for a page-context `fetch()` GET re-probe of a POST response
(confirmed again in ELITEA-1907) — same CORS redirect through
`dev.elitea.ai/forward-auth/...`. Use `browser_network_request(index,
part: 'response-body')` on the original request instead of re-fetching.

## ELITEA-1907: ResourceSuggestions/SuggestionItem — third independent
## testid-bare surface in the Agent "Build with AI" tree

`GenerateAgentReviewForm.jsx` renders `<ResourceSuggestions>` (one per
category: toolkit/mcp/pipeline/agent/skill) which renders `<SuggestionItem>`
per suggested resource. Confirmed (2026-07-16) both files have ZERO
`data-testid` anywhere — section title, card, checkbox, name text,
description text. This is a fourth surface (shell / wrapper / review-form
fields / **resource-suggestion sub-tree**) independent of the three already
tracked above — landing testids on the review-form's own TextFields would
NOT cover this one either. Suggested naming for whoever runs
`add-data-testid` next: `generate-agent-resource-section-{entityType}`,
`generate-agent-resource-item-{entityType}-{id}`,
`generate-agent-resource-checkbox-{entityType}-{id}`,
`generate-agent-resource-name-{entityType}-{id}`,
`generate-agent-resource-description-{entityType}-{id}` (dynamic,
`{entityType}-{id}` param order per this project's naming convention).

## ELITEA-1907: suggestion categories are inventory-gated, not just
## relevance-gated — thin test-project data silently hides whole sections

`ResourceSuggestions.jsx` returns `null` (renders nothing, not even the
section title) when its `items` array is empty. The generate-draft
response's `suggested_toolkits`/`suggested_agents`/`suggested_pipelines`/
`suggested_mcp`/`suggested_skills` arrays appear to be filtered from
**project-configured resources only** (not the toolkit-type catalog) AND
by relevance to the prompt. Confirmed live in project 399: zero configured
Toolkits at all (nav to `/toolkits/all` redirects to the empty
`/toolkits/create` state) → `suggested_toolkits` always `[]` regardless of
prompt; 6 configured Agents but none GitHub/Jira-relevant → correctly `[]`
for that prompt. **Before treating an empty suggestion category as a
suggestion-engine defect, audit the project's actual configured-resource
inventory for that category first** — an empty category is very often a
thin-fixture artifact of this shared dev-backend project, not a bug.
Corollary: a suggested resource's `description` in the response is a
straight pass-through of that resource's OWN description field — if you
need to prove the "card shows name + description" UI path, you need a
fixture resource that (a) is relevant to your test prompt AND (b) itself
has a non-empty description filled in. The one pre-existing relevant
resource in project 399 (`Remote Github` MCP, id 3) has an empty
description, so it can only prove the "name shown, description
correctly absent" half, not the "description shown" half.
