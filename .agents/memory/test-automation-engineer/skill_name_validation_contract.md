---
name: Skill name validation contract (EliteaUI create form)
description: The Skill `Name *` field validates kebab-case + max 64 chars + no claude/anthropic — cite this file, not memory prose
type: reference
---

Verified 2026-08-27 (ELITEA-1790 / issue #1811 fix round) against
`EliteaUI` `origin/main` (fresh `git fetch origin` first).

Source of truth:
`src/[fsd]/features/skill/lib/validation/skillValidationSchema.validation.js`

```js
const SKILL_NAME_MAX_LENGTH = 64;
const SKILL_NAME_RE = /^[a-z0-9]([a-z0-9-]*[a-z0-9])?$/;
```

The full contract the form enforces on a Skill name:

1. lowercase letters / digits / hyphens only, no leading or trailing hyphen
2. **at most 64 characters** — NOT 32 (a "max 32 characters" claim shipped in a
   test docstring on this branch and was caught at review as uncited; the real
   figure is 64)
3. must NOT contain `claude` or `anthropic` (`no-reserved-vendor` yup test) —
   easy to trip if a generated name embeds an arbitrary word
4. description / instructions use `MAX_DESCRIPTION_LENGTH` /
   `MAX_INSTRUCTIONS_LENGTH` from `@/common/constants`

The JS comment states it mirrors the backend rule
(`elitea_core models/pd/skill.py` → `validate_skill_name`), so the same limits
apply to API-created skills.

Same `SKILL_NAME_MAX_LENGTH = 64` is duplicated in three more places
(`skillDraftValidation.helpers.js`, `skillAIEditionSteps.constants.js`,
`GenerateSkillReviewForm.jsx`) — all agree.

**Lesson:** the qa-engineer memory note
`skill_form_and_export_import_quirks.md` documents the CHARSET only and carries
no length figure. Do not cite it for a length claim.
