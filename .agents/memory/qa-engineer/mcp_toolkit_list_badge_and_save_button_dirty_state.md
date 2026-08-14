---
name: MCP/toolkit list type badge is client-synthesized; Save button is dirty-based not validity-based
description: ELITEA-1921 discoveries - the "Remote"/"Local" type badge on entity-card list cards has no server-side tags field (client-synthesized via ToolkitsHelpers.enhanceToolkitData), and toolkit create-form Save buttons enable on first dirty field rather than on full required-field completeness
type: feedback
---

## MCP/toolkit list "type" badge (e.g. "Remote") is not server data

The `/mcps/all` (and likely `/toolkits/all`) list card's type badge — the
short text like "Remote" shown next to the author avatar — is NOT present
in the list API response (`GET .../elitea_core/tools/prompt_lib/{project}
?...`). Confirmed live: the raw JSON has no `tags` field on any row.

It is synthesized entirely client-side by `ToolkitsHelpers.enhanceToolkitData()`
(`EliteaUI/src/[fsd]/features/toolkits/lib/helpers/toolkits.helpers.js:310`),
which maps each toolkit's `type` through `getToolkitIcon()`'s schema-driven
`label` and injects `tags: [{id: type, name: label, data: {type}}]` before
handing the row to `Card.jsx`. `Card.jsx` renders that array via
`CardTagSection` -> `CardTagSectionItem`, which carries the **generic,
already-on-`main`** testid `entity-card-tag-chip` (shared across every
entity-list card type: agents, skills, pipelines, MCPs, credentials, ...).

**Automation implication:** don't look for a `tags` field in the list API
response, and don't assume a dedicated MCP-specific badge testid exists —
scope the existing generic `entity-card-tag-chip` inside the specific
`entity-card` (filtered by `entity-card-name` text) instead. No new testid
needed for this observable on any entity-list page that already uses
`Card.jsx`.

## Toolkit/MCP create-form Save button: dirty-based enable, not validity-based

On the Remote MCP create form (`/mcps/create/mcp`, and likely every other
`ToolBaseProperty.jsx`-driven create form), the Save button
(`toolkit-form-save-button`) is `disabled` on the pristine, untouched form —
but flips to `disabled: false` the instant **any single field** is touched,
not once all required fields hold values. Confirmed live via `page.evaluate`
DOM reads (not just snapshot rendering) for both "Name filled, Url empty"
and "Url filled, Name empty" — both produced `disabled: false`.

This is NOT a functional defect: clicking Save with required fields still
empty fires no network request at all — Formik/Yup client-side validation
intercepts the click, marks the empty required field `[invalid]` with a
"Field is required" inline message, and blocks submission. Filed as an
[INFO] clarification (`EliteaAI/elitea-testing-public#633`), not a bug.

**Automation implication:** assert Save `disabled` only on the pristine
form and `enabled` once ALL required fields are filled (matches the real
end-state case text usually wants). Never assert an intermediate
"still disabled after only one required field is filled" state — it will
be flaky/wrong, since Save is already enabled at that point. This pattern
likely generalizes to every `ToolBaseProperty.jsx`-schema-driven create
form (toolkits, applications, credentials), not just MCP — worth checking
if writing a similar Save-button-state test elsewhere in the suite.
