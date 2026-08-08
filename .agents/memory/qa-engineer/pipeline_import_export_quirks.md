---
name: Pipeline import/export quirks
description: Pipeline export downloads Markdown not JSON; Import shares Agent's ImportWizardModal; Task-field 400 is not an import defect
type: reference
---

Confirmed live 2026-08-08 (ELITEA-2012 analysis), `http://localhost:5173`.

- **Export is always Markdown (`.pipeline.md`), never JSON** — `ExportApplicationButton.jsx`'s
  `useExportApplication` hook calls `doExport({ format: ExportFormat.MD })()` unconditionally,
  same for Agents. Any TMS case text claiming "JSON file downloads" for an Elitea export is
  stale — file as a case-text-drift clarification, don't treat as a defect (reverse-masking
  guard). Filename: `<slugified-name>.pipeline.md`. Filed: `elitea-testing-public#1334`.
- **Import accepts only `.md`/`.zip`** (`useImport.hooks.js`: `fileInput.accept =
  '.md,.zip,text/markdown,application/zip'`) — exactly matches what Export produces, so the
  round trip works even when the case text says "JSON".
- **Pipelines' Import button has NO testid** (`src/pages/Pipelines/Pipelines.jsx:272`,
  `<ToolbarImportButton />` — no `testId` prop), unlike Agents
  (`src/pages/Applications/Applications.jsx:113`, `testId="agents-import-button"`,
  ELITEA-1795/EliteaUI PR #552). `ToolbarImportButton.jsx` already supports the prop — it's a
  one-line mechanical fix to thread `testId="pipelines-import-button"`.
- **Everything downstream already works for pipelines with zero new testid work** — the preview
  dialog, confirm button, and "Import Complete" dialog are the SAME shared `ImportWizardModal`
  Agent/Skill import use: `agent-import-preview-dialog`, `agent-import-confirm-button`,
  `agent-import-complete-dialog`, `agent-import-complete-got-it-button` (still `agent-` prefixed
  despite being entity-agnostic — don't rename, just reuse).
- **LLM node Task field left `Type=Fixed`/empty Value → chat send 400s**
  (`"messages.0: user messages must have non-empty content"`) — this is a GENERAL LLM-node
  execution precondition, NOT an import defect. Reproduced on the pre-export original too. Fix:
  `Type=Variable, Value=input` (via the shared `select-option-{}` dynamic testid convention:
  `select-option-variable` → `select-option-input`). Any pipeline case needing a real chat
  execution assertion must configure Task this way, or it will read as a false import/execution
  defect.
- Minor already-tracked cosmetic issue: Import Complete dialog's `IWModalSucceedContent.jsx` has
  a benign `validateDOMNesting` (`<div>` in `<p>`) console warning, same across Agent/Skill/
  Pipeline import — `elitea-testing-public#570`.
- **Export top-level YAML shape depends on whether the pipeline has a real (non-END) node**
  (confirmed live 2026-08-08, ELITEA-2050, on TWO independently-created pipelines): a
  node-less pipeline (only `END`) exports with NO top-level `entry_point`/`nodes` key at
  all — only `pipeline_settings.nodes` (canvas) lists the `END` entry. A pipeline with a
  real node exports WITH `entry_point: <id>` + a top-level `nodes:` list (per-node
  `type`/`input_mapping`/`output`/`transition`). There is NO literal top-level `state` key
  anywhere (confirmed via `useExport.js` source read — pure server-rendered `?format=md`
  fetch, no client "state" concept); a case asking to verify "state" in an export maps onto
  `pipeline_settings`, not a literal key. Any case-text drift about "JSON file downloads" on
  a NEW TMS case is the SAME underlying pattern as `#1334` (same object: `useExport.js`'s
  `doExport` hard-codes `format=md`, no JSON path exists) — comment on `#1334`, don't refile.
