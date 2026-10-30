---
name: Skill Instructions opens in Preview; Edit mode shows YAML frontmatter
description: On DEV the skill detail Instructions defaults to Preview; CodeMirror renders only in Edit and now prefixes name/description frontmatter — read via get_instructions_body()
type: feedback
---
ELITEA-1795 / #2674 (triage A). Click `click_edit_mode()` before reading `skill-instructions-editor-content`; use `SkillFormPage.get_instructions_body()` to strip the leading `---name/description---` block. Precedent: ELITEA-3366 (d2e89fd8). Local repro of CI failures needs `APP_PREFIX=/app` exported (no `.env.test` in the factory container -> /skills/create 404s without it).
