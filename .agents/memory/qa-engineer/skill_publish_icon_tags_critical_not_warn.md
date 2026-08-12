---
name: Skill Publish — missing icon/tags is CRITICAL/FAIL, not WARN
description: Skill Publish wizard (shared PublishWizardModal.jsx w/ agents) treats missing custom icon AND missing tags as deterministic critical_issues (FAIL, Publish disabled) — contradicts ELITEA-2598's WARN premise, filed as clarification #1463.
type: project
---

Discovered analysing ELITEA-2595/ELITEA-2596/ELITEA-2598
(`test-specs/skills/l2_skill-publishing-wizard-happy-path_ELITEA-2595.md` +
siblings). Same shared component as agents (`agent_publish_unpublish_wizard_mechanics.md`
already documents "no tags" as critical for agents) — this run additionally
confirmed **missing custom icon** is ALSO a deterministic critical gate for
skills, and re-confirmed tags.

**Live response shape** (`POST .../publish_skill_validate/prompt_lib/{project}/
{skillId}/{versionId}`): `{status, critical_issues[], warnings[], recommendations[],
counts, ...}`. Each issue entry carries `"source": "deterministic"` (rule-based,
stable across runs) or `"source": "ai"` (LLM-generated wording, content reliable
but exact phrasing varies). `canPublish = status !== "FAIL"` — ANY critical issue
blocks the Publish button.

**Deterministic CRITICAL gates (any one alone ⇒ FAIL):**
- `icon` — "No custom icon set"
- `tags` — "No tags defined" (zero tags)
- `description` — too short (live threshold: **50 chars**, not the "100" the
  ELITEA-259x case texts assume)
- `instructions` — too short (live threshold: **100 chars**)

**AI-sourced CRITICAL gates (also block):** placeholder markers (`[replace
this]`, `TODO:`) in description/instructions; hardcoded secrets/API-keys/
passwords in instructions.

**WARN-only (does NOT block):** generic/placeholder-like name (e.g. literal
`"skill"`); "description lacks action verbs".

**Consequence for any skill-publish happy-path fixture:** must include a
custom icon AND ≥1 tag AND meet the 50/100-char thresholds, or Validation
returns FAIL and the wizard never reaches Publishing — the case text for
ELITEA-2595 doesn't name icon/tags as prerequisites at all; ELITEA-2598
explicitly (and, per live evidence, incorrectly) claims missing icon is
WARN-level. Filed as clarification
https://github.com/EliteaAI/elitea-testing-public/issues/1463.

**Fast icon fixture:** the project-scoped "Uploaded" icon gallery
(`GET /upload_skill_icon/prompt_lib/{project}`) already has entries from
prior runs — `SkillFormPage.upload_skill_icon_edit_mode()` (ELITEA-2604) can
select an existing one, no fresh file upload needed for a disposable fixture.

**`publish-menuitem` testid is dynamically constructed**, not a JSX literal —
`DotMenu.jsx`: `` data-testid={testId ? `${testId}-menuitem` : undefined} ``
where `testId = item.key`; `SkillControls.jsx` sets `key: 'publish'` at the
call site. A plain `git grep -- "publish-menuitem"` finds NOTHING even though
the testid is real and live-confirmed — verify by reading the `key:` line +
the template instead of grepping the literal string (same trap as any
runtime-composed testid, `.agents/workflow.md` § Closure record stage-1 note).
