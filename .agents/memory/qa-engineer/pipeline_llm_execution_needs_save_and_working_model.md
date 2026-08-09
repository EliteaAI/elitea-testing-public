---
name: Pipeline LLM execution needs Save + a working model
description: Task-field fix requires Save (unlike module toggles); DEV's default model (Claude 4.5 Sonnet) 400s always — use gpt-5.2
type: reference
---

Confirmed live 2026-08-09 (ELITEA-2059 analysis), on the shared `test-pipeline`
fixture (id 6938):

- **Not every pipeline-config fix takes effect from live form state alone.**
  The "Attachments" MODULES switch gates the chat's attach-button availability
  INSTANTLY (pure formik state, `useAgentAttachments`, zero network) — no Save
  needed. But the LLM node's `task` input-mapping fix (`Type=Fixed`→`Variable`,
  `Value`→`input`, the ELITEA-2012-documented execution gotcha) does NOT take
  effect at execution/predict time until the pipeline is **saved**
  (`agent-save-button`). Symptom if you skip it: the model replies "I didn't
  receive any text or image in your last message" even though the UI shows
  the Task field correctly mapped. Don't assume "UI shows it configured" means
  "backend will use it" — some fields are read from persisted version data at
  predict time, not the live form.
- **The DEV backend's default pipeline-chat model 400s on EVERY message**,
  attachment or not: `Anthropic Claude 4.5 Sonnet` has no fallback model group
  configured (`"No fallback model group found for original
  model_group=1_eu.anthropic.claude-sonnet-4-5-20250929-v1:0. Fallbacks=[]"`).
  This reproduces on a plain "Hello" with zero attachments and zero other
  config issues — it's model-specific, not case-specific. Switching to
  **GPT-5.2** (`pipelines.select_llm_model("GPT-5.2")`,
  `pipeline_detail_page.py:6292`) works reliably. `PipelineAPI
  .create_pipeline_with_llm_node()` already defaults to
  `settings.default_model_name` = `"gpt-5.2"` — a FRESHLY created pipeline via
  that helper sidesteps this; only a pre-existing/shared fixture pipeline
  (like `test-pipeline` id 6938, whose default chat model may differ) needs
  the manual switch. If a pipeline-chat execution assertion 400s with this
  exact "No fallback model group" text, it's THIS gotcha — switch model,
  don't debug the pipeline config further.
- A bare `llm`-type node also can't extract an attached file's actual byte
  content (only sees a path reference in text) — expected node-architecture
  limit, not a bug; see `test-specs/pipelines/_surface.md` § "Attach Files in
  Chat" for the full writeup.
