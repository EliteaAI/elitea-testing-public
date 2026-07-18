---
name: Agent .md import — instructions must be body, not a frontmatter key
description: A hand-authored agent-import .md fixture must put Instructions as plain markdown BODY text below the closing `---`, never as a frontmatter `instructions:` key (silently ignored) — plus the Import-preview dialog's Main-entity card testid gap for Description/Instructions
type: feedback
---

## The fixture-format finding (ELITEA-1901)

When hand-authoring a `.md` file to upload through the Agents-list "Import"
button (`agents-import-button`), the YAML frontmatter must carry `name`,
`description`, and `model` (+ any other settings) — but **Instructions is the
plain markdown text BELOW the closing `---`, not a frontmatter key**.

Confirmed by two live attempts through the real Import → file chooser →
"Import parameters" preview dialog:

- `instructions:` as a frontmatter key (even a YAML block-scalar `|` value) —
  Description previewed fine; **Instructions rendered EMPTY**, both in the
  preview dialog and on the resulting Agent's detail page after confirming
  the import. Not an error, not a defect surfaced anywhere — just silently
  ignored.
- Moving the exact same text to the markdown body (nothing after `model:` in
  frontmatter, plain text following the second `---`) — Instructions
  previewed and imported **verbatim**.

This matches the app's own **export** shape already documented in
`test_export_agent_no_nested_dependencies.py` (ELITEA-1894:
`agent_body = parts[2].strip()` is asserted as the Agent's instructions) — the
import parser is consistent with the export format. Any TMS case text that
lists "instructions" alongside frontmatter keys (e.g. ELITEA-1901's Test Data
row: "YAML frontmatter (name, description, model, instructions)") is
imprecise wording, not a spec for a literal frontmatter key — filed as
CLARIFICATION EliteaAI/elitea-testing-public#628.

**Minimal valid fixture shape:**
```
---
name: my-agent-name
description: some description
model: gpt-5.2
---
The agent's instructions go here as plain markdown body text.
```

## The testid gap this surfaced (Import-preview dialog, Main-entity card)

Read directly from EliteaUI source
(`src/[fsd]/entities/import-wizard/ui/ImportWizardModal/`):

- `IWModalEntityCard.jsx` renders the **Description** field via a bare
  `IWModalEntityTextField` with NO `testId` prop passed — for ANY entity type
  (Main / Nested / Skill). It is never testid-addressable in the preview
  dialog.
- `IWModalDetails.jsx` only passes `instructionsTestId` to the **Nested**-entity
  card (`agent-import-preview-nested-agent-instructions`) and the **Skill**
  card (`agent-import-preview-skill-instructions`) — the **Main**-entity card
  (lines 76-80) gets `titleTestId`/`toggleTestId` only, no
  `instructionsTestId` at all. The Main entity's own Instructions preview text
  has no testid.

Only `agent-import-preview-name` (the title) is testid-backed for the Main
entity. If a future case needs to assert the Main entity's
Description/Instructions **verbatim inside the preview dialog itself** (not
just post-import), that's new `add-data-testid` work — ELITEA-1901's own
automation doesn't need it (the case only requires "entity card displayed",
and the verbatim check lands on the post-import detail page, which already has
full testid coverage: `agent-name-input`/`agent-description-input`/
`agent-instructions-input`).

## Related

- `agent_nested_agent_export_import_quirks.md` — the ELITEA-1902 nested-agent
  import/export quirks (zip format, always-new IDs).
- `agent_import_recreates_skills_quirks.md` — ELITEA-1795's Skill-recreation
  import quirks, same dialog family.
- CLARIFICATION filed: EliteaAI/elitea-testing-public#628.
- Pre-existing tracked console warning on the same "Import Complete" dialog
  (Tooltip `validateDOMNesting`): EliteaAI/elitea-testing-public#570.
