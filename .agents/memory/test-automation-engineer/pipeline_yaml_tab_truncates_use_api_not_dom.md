---
name: Pipeline YAML tab truncates — use API not DOM
description: pipeline-yaml-editor silently clips long documents; verify via pipeline_api.get_pipeline() instead
type: feedback
---

`get_yaml_content()` (`PipelineDetailPage`, reads `.cm-line` elements under
`[data-testid="pipeline-yaml-editor"]`) only shows what CodeMirror actually
rendered — and for a pipeline node whose full YAML exceeds roughly 32-34
lines at the project's default headless viewport (1366x768), CodeMirror
stops rendering partway through and never shows the rest, with **no
scrollbar offered** (`.cm-scroller.scrollHeight === .cm-scroller.clientHeight`
— the editor itself believes there's nothing more to show). This is a
CONFIRMED, already-filed product defect:
`EliteaAI/elitea-testing-public#1025` (first found ELITEA-2010, a Toolkit
node with 41 lines cut at line 32; reconfirmed ELITEA-2045, an LLM
structured-output node with 40 lines cut at line 34; reconfirmed again
ELITEA-2446, a plain 2-node LLM->Code->END pipeline with 2 custom state vars
— even a "short" multi-line Code-node script is enough to trip it). It is
display-only —
verified via the save PUT's response body, which always has the full,
correct YAML.

**Two confirmed facts, both matter:**
- Resizing the browser viewport TALLER (e.g. 1400x2200) makes the full
  document render — the root cause is viewport-height-driven, not a hard
  line-count cap. This is NOT a reliable fix for a shared test (viewport
  changes are per-test, awkward, and the exact line threshold isn't a
  stable contract) — treat it as diagnostic confirmation only, not the
  production fix.
- The real fix for any assertion needing the FULL pipeline YAML: read
  `pipeline_api.get_pipeline(pipeline_id)["version_details"]["instructions"]`
  (parsed with `yaml.safe_load`) instead of `switch_to_yaml_view()` +
  `get_yaml_content()`. Same pattern `test_pipeline_yaml_editor_invalid_syntax.py`
  (ELITEA-2068) and `test_pipeline_advanced.py` already use for server-truth
  readback — not a new convention, just the correct default whenever the
  case needs to assert something near the END of a multi-node/multi-field
  pipeline's YAML (e.g. `structured_output: true`, a later node's
  `transition`, anything past the first ~30 lines).

Before assuming the YAML tab will show what you need, do the line-count
math: STATE block (N custom vars × ~3-4 lines each) + node YAML (varies by
type, LLM nodes with SYSTEM/TASK/CHAT HISTORY + input_mapping run ~15-20
lines alone) adds up fast. If in doubt, verify via the API from the start
rather than discovering the truncation mid-implementation.
