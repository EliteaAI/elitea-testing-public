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

## ELITEA-1909: nested-Agent suggestion needs a relevant Agent in inventory
## too — same inventory-gating pattern, confirmed for the Agent category

The empty-category-hides-section finding above (ELITEA-1907) was only
confirmed for Toolkits/MCPs at the time. ELITEA-1909 (2026-07-16) confirms
the identical rule applies to the "Suggested Agents:" category: with zero
Agents in project inventory semantically relevant to the generation
prompt, `suggested_agents` is always `[]` and the whole section is hidden
(same `ResourceSuggestions.jsx:10` conditional). To get an Agent suggested
for testing/exploration purposes, create at least one Agent beforehand
(via `AgentAPI.create_agent_full()` — see below for why not
`create_agent()`) whose name+description is semantically relevant to the
prompt you're about to submit to "Build with AI". Two agents both relevant
to the same prompt will BOTH surface as suggestions, which is the easiest
way to get a genuine "select one, leave one unselected" fixture pair for
any case needing to prove non-selected-resources-stay-absent.

**Case-text implication:** ELITEA-1909's own stated preconditions never
mention this — same gap shape as ELITEA-1907 found for Toolkits, but
ELITEA-1909 is the first case that actually needs to exercise the Agent
category (selecting + attaching it), not just observe it rendering. Filed
as CLARIFICATION `elitea-testing-public#572`. If a future case needs
Pipelines/Skills suggested too, expect the same gating rule to apply —
check inventory before assuming an empty category is a bug.

## ELITEA-1909: selected resources are NOT attached in the create-agent
## POST — two separate PATCH calls follow, and nested-Agent attachment
## uses an internal wrapper id, not the Agent's own application id

`GenerateAgentModal.jsx`'s approve flow makes THREE sequential network
calls, not one atomic create:
1. `POST /applications/prompt_lib/{project}` → `201` — creates the base
   agent. **The response's `version_details.tools` is `[]` here** — do
   not read this as "attachment failed"; it hasn't happened yet.
2. `PATCH /tool/prompt_lib/{project}/{toolkit_id}` → `201`, once per
   selected Toolkit/MCP (`associateToolkit`, `Promise.allSettled`).
   Response: `{"has_relation": true, "tool_id": {toolkit_id}}`.
3. `PATCH /application_relation/prompt_lib/{project}/{app_id}/{version_id}`
   → `201`, once per selected Agent/Pipeline (`associateApplications`).
   Response: `{"has_relation": true, "tool_id": {internal_wrapper_id}}`
   — **this `tool_id` is NOT the selected Agent's own `application_id`**.
   Confirmed live: selecting Agent id `4971` produced a response `tool_id`
   of `1328`, a completely different number. The platform wraps a
   selected Agent as an internal "tool" entity (the "application-as-tool"
   pattern — see the `elitea-toolkit` skill) when nesting it inside
   another agent. Don't assert equality between the two ids.

Zero association calls fire for anything left unchecked — confirmed by
filtering the full network log for both endpoint patterns and finding no
call referencing the unselected agent's id.

## ELITEA-1909: `agent-toolkit-card` (detail-page Tools section) is
## intentionally shared/non-templated across Toolkit AND nested-Agent
## cards — don't add a redundant dynamic testid, reuse the existing
## `.filter(has_text=...)` pattern

Unlike the review-form's `SuggestionItem.jsx` cards (which got proper
`{entityType}-{id}` templated testids via ELITEA-1907's `add-data-testid`
pass), the CREATED agent's detail-page "Tools" section renders every
attached resource — Toolkit, MCP, nested Agent, nested Pipeline — through
one shared `ToolCard.jsx` component carrying a single static
`data-testid="agent-toolkit-card"`, identical for every card regardless
of entity type. This looks like a gap at first glance but isn't: the
project already has a proven disambiguation pattern for exactly this —
`AgentDetailPage.is_toolkit_attached(toolkit_name)`
(`automation/pages/agent_detail_page.py:1063`) does
`self.toolkit_card.filter(has_text=toolkit_name).first...`, and it
predates this case (used since at least ELITEA-1950's MCP-attach work).
It works identically for a nested-Agent card's name, since both card
types share the same component and testid. **Reuse this method for BOTH
Toolkit-presence and nested-Agent-presence assertions** rather than
inventing a new templated testid — `add-data-testid` should NOT touch
`ToolCard.jsx` for this reason unless a future case specifically needs to
target a card by something other than its visible name text.
