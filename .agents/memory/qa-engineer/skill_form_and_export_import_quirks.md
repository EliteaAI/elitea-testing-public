---
name: Skill form and export/import quirks
description: Skill name is kebab-case only (case examples with spaces/caps fail); overflow menu has two logical groups (VERSION vs SKILL) with distinct Export/Delete items; exported .md has no version: frontmatter key
type: feedback
---

Discovered while analysing ELITEA-1737 (Import Skill Base Version, localhost:5173):

- **Skill `Name *` field is kebab-case only**: lowercase letters, digits,
  hyphens; no spaces, no leading/trailing hyphen. Client-side validation
  blocks Save with the message "Name must be lowercase letters, digits and
  hyphens only (no spaces), and cannot start or end with a hyphen." TMS case
  example names like `"Test Export Skill"` will fail this — always use
  kebab-case (`elitea-XXXX-some-skill`) when scripting Skill creation.
- **Skill detail page's overflow/controls menu (`skill-controls-menu-button`)
  has two logical groups**, separated by a "VERSION" / "SKILL" divider:
  - VERSION group: Export (`data-testid="export-version-menuitem"`), Share,
    Fork, Publish (disabled/"Soon"), Delete (disabled — version delete not
    yet wired).
  - SKILL group: Share, Pin to top, Delete skill
    (`data-testid="skill-delete-menu-item"`).
  Don't confuse the two "Share" items or the two "Delete" items — always
  target by testid, not by accessible name alone (names collide across
  groups).
- **Delete-skill confirmation dialog requires typing the exact skill name**
  into an unlabelled textbox before the Delete button enables — plan for
  this in any UI-based cleanup helper.
- **Exported `.md` file format**: YAML frontmatter with `name`,
  `description`, `tags` (list) only — **no `version:` key** — followed by
  the instructions as the plain markdown body after the closing `---`. The
  version is not literal in the file; re-importing still correctly shows
  "Version: base" in the import-parameters dialog, so this is expected
  behavior, not a defect (filed as clarification, not a bug —
  github.com/EliteaAI/elitea-testing-public/issues/21).
- **Import flow**: Skills-list page toolbar has an "Import" button (top
  right, no testid yet) → native file chooser → uploading a valid `.md`
  opens an "Import parameters" dialog showing PROJECT / entity name / "Type:
  Skill | Version: base" / description / instructions preview → clicking
  the dialog's own "Import" button (same accessible name as the toolbar
  button — must scope by dialog when asserting) creates a new skill with a
  fresh unique ID and shows toast "Skill imported successfully."
- Full AFS: `test-specs/skills/l3_import_skill_base_version_ELITEA-1737.md`.
