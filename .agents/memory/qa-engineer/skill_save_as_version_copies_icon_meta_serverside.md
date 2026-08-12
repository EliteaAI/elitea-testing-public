---
name: Skill Save As Version copies icon_meta server-side
description: ELITEA-2606 finding — new-version POST response already carries the base version's icon_meta; base version unaffected.
type: project
---

Confirmed live (2026-08-12, ELITEA-2606 analysis): `SkillDetailPage.
save_as_version()`'s underlying `POST /api/v2/elitea_core/skill/prompt_lib/
{project}/{skillId}` ("create version") response body already includes
`meta.icon_meta` for the new version, byte-identical URL to the base
version's icon — this is a server-side copy at version-creation time, not a
client-state carryover. Verified further via a full hard reload of the new
version's URL. Switching back to `base` afterward shows the base version's
icon unaffected. No product defect; no testid gaps (every locator on this
flow — `skill-form-icon-img`, `skill-save-as-version-button`,
`skill-create-version-*`, `skill-version-select(-combobox)`,
`version-option-{name}` — is pre-existing).

Same `meta.icon_meta` shape/guarantee as Fork (ELITEA-2602/ELITEA-2603,
"preserved by reference"), but a DIFFERENT endpoint
(`skill_export_fork` vs this plain "create version" POST) — don't assume a
regression in one implies the same in the other.

`SkillAPI.get_skill(skill_id)` (automation/api/client.py:1460) cannot target
a SPECIFIC version's icon — always hits the bare `/skill/prompt_lib/
{project}/{skillId}` endpoint, no `versionId` segment. If an implementer
wants an API-level per-version icon assertion, it needs a small additive
`version_id` param extension.

Full detail: `test-specs/skills/l3_skill-custom-icon-persistence-on-save-as-version_ELITEA-2606.md`
and `test-specs/skills/_surface.md` § "Custom icon persists across Save As
Version".
