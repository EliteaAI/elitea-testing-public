---
name: Pipeline export frontmatter split "---" corruption
description: raw_content.split("---", 2) truncates YAML mid-doc when an edge id embeds "---"; use re.split(r"(?m)^---\s*$", ..., maxsplit=2) instead
type: feedback
---

## What happened (ELITEA-2050, extending `test_pipeline_import_via_file.py`)

The `.pipeline.md` export's YAML frontmatter is parsed in several specs via
`parts = raw_content.split("---", 2)`. This is unsafe: ReactFlow edge ids are
built as `xy-edge__{source}---{target}` (e.g.
`xy-edge__LLM 1---EliteAPipelineEnd`), and that literal `---` substring is a
false match for a naive string split — it truncates the "document" mid-way
through `pipeline_settings.edges`, silently dropping everything after it
(`pipeline_settings.nodes`, `orientation`, `layout_version`, and any field
that happens to sit later in the file).

It went unnoticed in ELITEA-2012 because all of its assertions
(`name`/`description`/`agent_type`/`conversation_starters`) target fields
that appear **before** `pipeline_settings` in the document — the truncation
never touched them. ELITEA-2050 needed `pipeline_settings.nodes`, which sits
**after** the corrupting edge id, and failed with
`pipeline_settings.nodes` silently absent (`{'edges': [...]}`, no `nodes`
key) until the parser was fixed.

## Fix

YAML frontmatter delimiters are only valid on their own line — split on a
line-anchored regex instead of a bare substring:

```python
import re
parts = re.split(r"(?m)^---\s*$", raw_content, maxsplit=2)
```

Confirmed live: this correctly captures `pipeline_settings.nodes` (2 entries:
LLM node + END) where the naive split lost it.

## Where else this pattern exists (not yet fixed — same latent bug, scope-fenced to my PR)

`grep -rn 'split("---"' automation/tests/` (2026-08-08) also hits:
`test_import_agent_zip_nested_agent_dependencies.py:237`,
`test_skill_export_import.py:160,418`,
`test_export_agent_with_attached_skills.py:231`,
`test_export_agent_no_nested_dependencies.py:230`,
`test_export_import_prompts.py:76,455`,
`test_export_import_pipelines.py:174,540` — any of these asserting a field
that appears AFTER an edge/id-bearing section (pipeline_settings, node
lists with dashed ids) is at the same silent-truncation risk. Worth a
scoped tech-debt sweep; not fixed here (each is its own file, out of this
PR's extend-existing scope).
