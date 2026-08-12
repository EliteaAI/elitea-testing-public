---
name: Agent publish/unpublish wizard mechanics
description: Publish is a 3-step AI-validated wizard that clones the Draft version into a new Published version (original Draft is untouched); Unpublish reverts that clone. Tags field rejects hyphens (different regex than version-name). Testids added ELITEA-1892.
type: project
---

Discovered analysing ELITEA-1892 (`test-specs/agents/l2_publish-draft-version-status-changes-unpublish-available_ELITEA-1892.md`).
Relevant source: `EliteaUI/src/[fsd]/entities/version/{ui,lib/hooks}/*Publish*`, `*Unpublish*`.

**Publish clones, it doesn't flip in place.** Clicking Publish on a Draft version
(`POST /publish/prompt_lib/{project}/{draftVersionId}`) creates a **brand-new version**
carrying Published status; the original Draft version is left untouched. The response's
`source_version_id` (and the post-publish navigation URL / VERSION dropdown) is the id you
need to assert against for "is it Published now" — never the id you started with. Unpublish
(`POST /unpublish/prompt_lib/{project}/{publishedVersionId}`) targets that clone's id directly
and reverts *it* to Draft.

**Publish is a 3-step wizard with an AI content-quality gate, not a single name field.**
`PublishWizardModal.jsx`: Preparation (version name + Category dropdown + "I agree with the
Publishing Terms" checkbox — all three required to enable Continue) → Validation
(`POST /publish_validate/...`, an LLM-driven check returning Critical/Warning/Suggestion; any
Critical issue — commonly "no tags" or "instructions missing/too thin" — disables the Publish
button with a `422`) → Publishing. Seed disposable test agents with a real instructions
sentence + at least one tag to pass validation on the first attempt.

**Tags field character set is stricter than the version-name field.** Tags: alphanumeric +
whitespace + comma + underscore only — **hyphens are silently rejected**
("Only alphanumeric characters, white space, comma and underscore allowed"). Version name:
`/^[a-zA-Z0-9._-]*$/` — hyphens ARE allowed there. Don't reuse a hyphenated slug (e.g.
`elitea-1892`) as a tag value; use underscores or an existing tag suggestion instead.

**Wizard fields don't persist across Cancel+reopen** — always re-fill Preparation step fully
every time the dialog opens in automation.

**Testids added this run (commit `a1914991`, EliteaAI/EliteaUI `automation/testids`):**
`publish-version-menuitem`, `unpublish-version-menuitem` (via `DotMenu`'s existing
`item.key` → `{key}-menuitem` mechanism — just add a `key` to the menu-item object, same
pattern as the sibling `delete-version` item), `agent-publish-version-name-input`,
`agent-publish-category-select`, `agent-publish-agree-checkbox`,
`agent-publish-continue-button`, `agent-publish-confirm-button`,
`agent-unpublish-confirm-button`. NOT added (out of touched scope): Cancel/Close buttons in
either dialog, the `isAdminPublish`-only branch (public-project publish flow), the
`showReason` admin-only textfield in `UnpublishConfirmModal.jsx`.

**Known defect filed:** #611 — the wizard's Stepper custom `stepIcon` (`CheckedIcon`) leaks
MUI's injected `completed`/`active`/`error`/`ownerState` props onto the DOM `<svg>`, 4 console
warnings every time the Publish wizard's Stepper renders. Cosmetic/console-only, isolated to
`PublishWizardModal` (confirmed a pure-Unpublish pass has 0 console errors). Use
`expect.soft()` + `# Known defect: #611` rather than hard-failing on console-clean assertions
for this flow.

**Case-text clarification filed:** #612 — ELITEA-1892's steps describe Publish as a single
version-name dialog; live product is the 3-step wizard above. Product is correct, case text is
stale (reverse-masking).
