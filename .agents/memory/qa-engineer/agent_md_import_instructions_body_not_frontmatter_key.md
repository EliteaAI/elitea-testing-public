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

## Reviewer-verified (PR #629, ELITEA-1901 implementation review)

Don't take a CLARIFICATION disposition at face value even when the analyst's
live-UI observation looks solid — cross-check against the actual frontend
source when the PR review dispatch explicitly asks for it (or when the finding
is load-bearing for the fixture shape every future import test will copy).
Dispatched an independent code-reading pass against EliteaUI (not the analyst's
notes) and confirmed the claim exactly:

- `src/[fsd]/entities/import-wizard/lib/helpers/importWizardParser.helpers.js`
  — `buildInstructionsBasedOnType()` (line 83) returns `{ instructions: body }`
  **exclusively** from the parsed markdown body; zero references anywhere in
  the import-wizard module to `frontmatter.instructions`. Same body-only
  contract independently in `useSkillImport.hooks.js:54`
  (`instructions: body || ''`) for the standalone Skill import flow.
- The **same parser** demonstrably CAN read an `instructions:` frontmatter key
  when that's the intended contract — it does, for nested `skills:` blocks
  (`buildSkillsFromFrontmatter`, line 142: `instructions: block.instructions ||
  ''`). This is the decisive point: the body-only shape for the TOP-LEVEL
  agent/skill is a **deliberate structural choice**, not a YAML-parsing
  accident or an oversight — ruling out "maybe the analyst just wrote bad
  YAML" as an alternative explanation.
- Export is 100% backend-generated (frontend only downloads the blob via
  `GET .../export_import/prompt_lib/{project}/{id}?format=md`), so the "export
  produces the same shape" half of the argument can't be verified from
  EliteaUI source alone — but it's consistent with the already-merged
  `test_export_agent_no_nested_dependencies.py:239` assertion (`agent_body =
  parts[2].strip()`, no `instructions` key present in the parsed frontmatter
  dict at all).

**Separate, adjacent finding (not filed, not blocking any PR):** the parser's
silent-drop-with-no-warning behavior when a plausible `instructions:`
frontmatter key IS present is its own low-severity product UX/robustness gap —
distinct from #628's "case text is imprecise" framing. Worth a standalone
low-severity ticket if this area gets touched again; not required for #628 or
for shipping ELITEA-1901's automation.

**Also cross-checked (same PR review):** the Axis-2 Model-selector addition in
ELITEA-1901's test isn't a red herring — `model-selector-name`/
`model-selector-button` (used via `AgentDetailPage.get_selected_model_name()`)
reflects the Agent's own persisted `model` config, not a decoupled
chat-panel-only preference. Confirmed two ways: (1) via the already-merged
`test_agent_llm_selector_anthropic_models.py`, which asserts this exact widget
is persisted via `PUT .../application/prompt_lib/... -> 201`; (2) via a direct
EliteaUI source trace — `LLMModelSelector.jsx:83/101` render the two testids
off a `selectedModel` prop with no internal logic; that prop is computed in
`LLMModelSelectorWrapper.jsx:33` from Formik's `version_details.llm_settings.model_name`,
which for a normal (non-public) agent is populated straight from
`useGetApplicationVersionDetailQuery`'s `GET /version/prompt_lib/{project}/
{agent}/{version}` response (`AgentEditor.jsx:205-214`, `api/applications.js:449-456`)
— i.e. the real persisted agent-version record. A fallback effect
(`LLMModelSelectorWrapper.jsx:46-60`) only kicks in when `model_name` is
empty/missing, never overriding an already-configured model. (The one
exception — a Public/shared agent's `entity_settings.llm_settings` override —
doesn't apply to a freshly-imported, non-public agent like ELITEA-1901's.)
Reusable fact for any future case that wants a "free" Model-field check via
this same testid on a normal (non-public) agent.

## Related

- `agent_nested_agent_export_import_quirks.md` — the ELITEA-1902 nested-agent
  import/export quirks (zip format, always-new IDs).
- `agent_import_recreates_skills_quirks.md` — ELITEA-1795's Skill-recreation
  import quirks, same dialog family.
- CLARIFICATION filed: EliteaAI/elitea-testing-public#628.
- Pre-existing tracked console warning on the same "Import Complete" dialog
  (Tooltip `validateDOMNesting`): EliteaAI/elitea-testing-public#570.
