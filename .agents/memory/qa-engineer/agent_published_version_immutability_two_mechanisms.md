---
name: Agent published-version immutability — two distinct enforcement mechanisms
description: Name/Description/Instructions/Tags stay editable and fail server-side on Save (400); Skill/Tool attach controls are disabled client-side pre-emptively — don't assume one wait/assert strategy covers both
type: feedback
---

## Context

Found during ELITEA-2614 (Published Agent Version Cannot Be Modified) analyst pass, localhost:5173,
agent detail page (`/agents/all/{id}/{versionId}?viewMode=owner`) on a `published` version.

## Findings

1. **General-section form fields (Name/Description/Instructions/Tags) are NOT disabled/read-only on a
   locked (published/embedded) version.** They stay freely typeable — confirmed live by typing into
   `agent-name-input` on a published version and watching the top-bar `Save` button go from
   `[disabled]` to enabled. Enforcement is entirely server-side: clicking `agent-save-button` fires
   `PUT /api/v2/elitea_core/application/prompt_lib/{project}/{agent_id}` → `400 Bad Request`,
   `{"error": "Version id {versionId} is published and can not be updated"}`. The UI renders this
   verbatim server string in a toast/alert — no separate client-copy exists.
2. **Skill/Tool attachment controls, by contrast, ARE disabled pre-emptively client-side.** Both
   `ApplicationSkills.jsx` and `ApplicationTools.jsx` compute
   `isVersionLocked = versionStatus === 'published' || versionStatus === 'embedded'` and pass it down
   as a `disabled` prop — the "+Skill"/"+Toolkit"/"+MCP"/"+Agent"/"+Pipeline" add buttons and the
   per-attachment remove/version-change controls are all `[disabled]` with NO network request firing
   on a blocked click attempt.
3. **Don't reuse one assert helper for both.** General fields: type → Save → wait for the `PUT`
   response → assert `status == 400` + `response.json()['error']` contains the expected substring →
   assert the toast text → `Discard` (which itself opens an "Are you sure you want to discard
   changes?" confirm dialog, `discard-confirm-button`) to reset before the next field. Attachment
   controls: assert `to_be_disabled()` directly, no click/no network wait needed.
4. **A rejected Save does NOT auto-revert the form** — the field keeps showing the rejected value
   until `Discard` is explicitly clicked and confirmed.
5. **Tooltip coverage for "why disabled" is inconsistent across the locked-version controls** — see
   `agent_skill_card_remove_control_quirks.md` point 5 and filed defect
   [EliteaAI/elitea-testing-public#1470](https://github.com/EliteaAI/elitea-testing-public/issues/1470).
   Tools' 4 add buttons + Skill's "+Skill" add button correctly show an immutability tooltip; the
   SkillCard remove button and `SkillVersionSelector` trigger do not.

## Where used

`test-specs/skills/l2_published-agent-version-cannot-be-modified_ELITEA-2614.md` (Parts B/C, Coverage
Map, Automation Hints).
