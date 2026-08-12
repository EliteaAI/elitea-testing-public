---
name: Agent publish validation-token error code differs from Skill's
description: Agent-entity publish_validate/publish "modified since validation" 400 uses error=validation_failed, NOT validation_token_invalid (the Skill-entity code from ELITEA-2597); assert both error+msg, not msg alone. Also skill-card-remove-button testid repeats per card — scope by parent skill-card-{id}.
type: project
---

## What (ELITEA-2601 live analysis, 2026-08-12)

The shared `PublishWizardModal.jsx` / publish-token-invalidation mechanism (stale
token after the entity's version was modified post-validation) exists for BOTH the
Skill entity (ELITEA-2597) and the Agent entity (ELITEA-2601), but the two entities
return **different `error` codes** for the functionally identical condition:

- Skill entity (ELITEA-2597's AFS): `400 {"error": "validation_token_invalid", ...}`
- Agent entity (confirmed live, ELITEA-2601): `400 {"error": "validation_failed",
  "msg": "Agent was modified since validation. Please re-validate."}`

Trigger confirmed live for the Agent entity: holding a validated (`Critical: 0`)
Publish wizard open in one browser tab, then **attaching a skill** to the SAME agent
version from a second tab, then clicking Publish in the first tab. The `msg` text
"Agent was modified..." is CORRECT for this entity (unlike the Skill flow, where the
same wording is a known, separately-filed MINOR copy-paste defect,
https://github.com/EliteaAI/elitea-testing-public/issues/1465 — that flow's `msg`
should say "Skill", not "Agent").

**Implication for any test asserting this error family**: assert on BOTH `error` code
AND `msg` text — don't reuse a `validation_token_invalid` expectation across entities,
and don't assert `msg` alone (two different `error` codes can carry near-identical
`msg` wording).

## Other confirmed handles from the same run

- `skill-card-remove-button` (agent's attached-skill card, hover-revealed,
  `aria-label="remove skill"`) is **NOT unique** — the same testid repeats on every
  attached skill card. Scope it inside the specific card's own
  `[data-testid="skill-card-{skill_id}"]` container.
- Second-tab navigation to an agent's Skills/config panel needs
  `?destTab=configuration&viewMode=owner` — a bare `/agents/all/{id}` URL lands on the
  Chat tab instead, silently hiding the Skills section.
- `publish_validate`'s per-attached-skill Critical checks are independent rules: a
  skill can fail "too short" and "contains placeholder text" as TWO separate,
  independently-attributed `critical_issues[]` entries (`skills [skill: <name>]:` prefix
  on both), not one merged message.

Full AFS: `test-specs/skills/l2_agent-with-skills-validation-attribution-and-token-invalidation_ELITEA-2601.md`
