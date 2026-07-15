---
name: Agent create 400 — temperature vs reasoning_effort conflict blocks all new agents
description: Deterministic critical blocker (issue #524) — plain /agents/create Save fails 400 whenever the project's default model is reasoning-capable; /agents/all was found completely empty for project 399 as a result
type: feedback
---

## Context

Found during ELITEA-1889 analyst pass (issue #67, "Agent Save As Version preserves
all attached Skills"), localhost:5173, project `Private` (id 399).

## Finding

A plain `/agents/create` form (Name + Description only, no model/LLM settings
touched) fails Save with a `400 Bad Request` on
`POST /api/v2/elitea_core/applications/prompt_lib/399`:

```json
[{"type": "value_error", "loc": ["versions", 0, "llm_settings"], "msg": "Value error, temperature is not allowed together with a reasoning_effort (other than 'none') — reasoning models reject a custom temperature"}]
```

Reproduced **2/2** in fresh, independent page loads (separate `browser_navigate`,
no shared session state, real `click()`/`pressSequentially()` only — no synthetic
input). The page never navigates away from `/agents/create`; a console warning at
`useCreateApplication.jsx:92` carries the identical `value_error`.

**Root cause hint**: `GET /api/v2/configurations/models/399?include_shared=true`
shows the project's default model is `eu.anthropic.claude-sonnet-4-5-20250929-v1:0`
("Anthropic Claude 4.5 Sonnet") with `"supports_reasoning": true`. 10 of the 11
models configured for this project carry `supports_reasoning: true` (only
`gpt-5-mini` doesn't) — the create form's default `llm_settings` payload appears to
still populate a non-null `temperature` alongside a non-`'none'` `reasoning_effort`
for such models, which the backend's pydantic validator now rejects. This reads as
a systemic regression, not a one-model edge case.

**Blast radius**: `/agents/all` was confirmed **completely empty** for project 399
at the time of this finding — meaning every case/session that needs a *fresh* Agent
(not reusing a pre-existing one) is currently blocked, project-wide, until this is
fixed. This is much bigger than ELITEA-1889's own scope.

**Filed**: [EliteaAI/elitea-testing-public#524](https://github.com/EliteaAI/elitea-testing-public/issues/524)
(CRITICAL, label `bug`, "Found while working #67").

## What still works

The "Save As Version" UI pattern itself is NOT broken everywhere — confirmed live
that the Skill detail page (`/skills/all/{id}`) has an enabled "Save As Version"
button next to disabled Save/Discard. The blocker is specifically Agent *creation*,
not the versioning mechanism in general.

## For future sessions

- Before starting any case that needs a **freshly created** Agent, check
  `/agents/all` first and/or try a throwaway create — if this defect is still open,
  don't burn time debugging your own test data; it's environment-wide.
- If #524 is closed, re-verify this note is stale before trusting it (delete/update
  once confirmed fixed).
- Once unblocked, ELITEA-1889 itself still needs a **fresh exploration pass** for
  Steps 2–4 (Save As Version dialog, version-name entry, how an Agent's saved
  versions are opened/switched-to) — none of that UI was ever seen live, so no
  handles exist for it yet (see the AFS's Blocked Steps section,
  `test-specs/agents/lcritical_agent-save-as-version-preserves-skills_ELITEA-1889.md`).
