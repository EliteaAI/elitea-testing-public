---
name: Skill Fork wizard quirks
description: Skill Fork reuses agent-* import-wizard testids verbatim except a generic fork-menuitem; preview omits tags; non-base fork normalizes to "base"
type: project
---

Executed ELITEA-2602 (Fork Skill End-to-End) and ELITEA-2603 (Fork Non-Base
Skill Version) live, full flow, localhost:5173.

- **Same shared `ImportWizardModal`/`IWModal*` tree as Agent (ELITEA-1893)
  and Pipeline (ELITEA-2051) Fork** — `agent-import-preview-dialog` /
  `agent-import-complete-dialog`, `agent-import-wizard-project-select-combobox`,
  `select-option-{projectId}`, `agent-import-preview-name`,
  `agent-import-preview-card-toggle`, `agent-fork-confirm-button`,
  `agent-import-complete-got-it-button` — all confirmed live for Skills,
  zero new testids needed for the wizard body.
- **Fork menuitem is DIFFERENT from the Agent/Pipeline pattern.**
  `SkillControls.jsx` implements Fork as its own `key: 'fork'` menu item via
  a dedicated `useForkSkill()` hook — NOT the shared
  `ForkEntityButton.jsx`/`useForkEntityMenu()` hook Agent/Pipeline/Toolkit
  use. Result: testid is the GENERIC `fork-menuitem`, not
  `agent-actions-fork-menuitem`/`pipeline-actions-fork-menuitem`. Still
  unique within the menu, works fine as a locator — just don't assume
  naming parity.
- **The "Main entity" preview card NEVER shows Tags**, for any entity type
  (Agent/Pipeline/Skill share the component) — only Name/Type/Description/
  Instructions render. Case ELITEA-2602 step 7 says "tags, etc." — filed as
  clarification (case-text overstatement, not a bug):
  https://github.com/EliteaAI/elitea-testing-public/issues/1455.
- **Non-base version fork**: the wizard preview shows the ACTIVE version's
  instructions (confirmed via `skill_export_fork` GET firing with that
  version's id), and the resulting forked skill's version is always
  named `"base"` in the target project with `meta.parent_version_id`
  pointing at the SOURCE's specific (non-base) version id — not its base.
  Confirmed via direct API response inspection, not just DOM.
- **Icon preserved by reference** — forked skill's `icon_meta.url` is
  byte-identical to the source's (same file path under the SOURCE
  project's storage folder), even cross-project. Not a defect.
- **Two testid gaps on skill icon upload** (confirmed via source read,
  `EliteaUI/src/[fsd]/features/skill/ui/skill-details/form/CreateSkillForm.jsx`
  + `EliteaUI/src/components/SelectIconDialog.jsx`): `EntityIcon` in
  `CreateSkillForm.jsx` passes no `data-testid` (Agent's equivalent got
  `agent-form-icon-button` for ELITEA-1899, Skill never did — needs
  `skill-form-icon-button`); `SelectIconDialog`'s Upload `IconButton` has
  no testid at all, affects every entity type using this shared dialog
  (needs `agent-icon-picker-upload-button` or entity-agnostic equivalent).
  Same two-click-to-open quirk as the Agent icon avatar applies here too
  (automation-only artifact, not a product bug).
- **Cross-project direct-URL nav 404s** — `GET
  .../skill/prompt_lib/{currentlySelectedProjectId}/{id}` uses the
  SIDEBAR's currently-selected project, not anything in the visited URL.
  Switch `project-selector-trigger-combobox` → `select-option-{id}` BEFORE
  navigating to a detail page in a different project.
- **Tags field rejects hyphens** (same root cause as
  `skill_tags_field_hyphen_rejected_and_chip_delete_icon_only.md` /
  issue #1445) — both cases' literal test data (`test-tag`, `fork-demo`,
  `v2-tag`) silently fails; substituted underscore variants. Commented the
  new occurrence on #1445 rather than re-filing. **Create-Version dialog's
  Name field does NOT share this restriction** — `v2-enhanced` (hyphenated)
  is accepted there fine. Don't assume one validation ruleset for the whole
  skill surface.
- AFS: `test-specs/skills/l2_fork-skill-end-to-end_ELITEA-2602.md`,
  `test-specs/skills/l3_fork-non-base-skill-version_ELITEA-2603.md`.
  Digest updated: `test-specs/skills/_surface.md` § Fork wizard — skill
  entity.
