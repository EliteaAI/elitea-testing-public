---
name: Hard-coded model display names rot — check the case before substituting one
description: A test naming a model the TMS case never named is a test artifact; delete the step, don't swap the literal
type: feedback
---

# Hard-coded LLM model display names rot — and the fix is usually deletion

**Verified 2026-09-09** (ELITEA-0679 / card #2112, live against `localhost:5173` +
`dev.elitea.ai` API, project 399).

## The failure shape

`ChatPage.select_model("GPT-5.2")` → `[role="menuitem"]:has-text("GPT-5.2")` →
`Locator.wait_for: Timeout 10000ms exceeded`. Deterministic, 3/3, on any environment.
The **menu opens fine** — it is the second `wait_for` (the option) that dies, so the call
log names the dead literal explicitly. Read the call log; the pytest tail alone looks like
a generic model-selector timeout and invites a wrong "outage" verdict.

## The catalog moves under you

`GET {ELITEA_API_BASE}/configurations/models/{project}?include_shared=true` is the source
of truth (it also reports which entry is `default: true`). As of 2026-09-09, project 399
has 8 models; `gpt-5.2`, `gpt-5.4`, `gpt-5.4-mini` are gone from every working project
(they survive only in global project 1 and are NOT surfaced even with
`include_shared=true`). Default is `Anthropic Claude 4.5 Sonnet`
(`eu.anthropic.claude-sonnet-4-5-20250929-v1:0`). `automation/config.py`'s
`default_model_name = "gpt-5.2"` is also dead (issue #2117).

**The product does not error on an unknown model — it silently substitutes `modelsList[0]`.**
So an API-seeded object built with a dead model name still "works", and only a UI selector
that has to *find the menu item* goes red.

## The judgment that matters

**Before swapping in a new model literal, read the TMS case.** If the case names no model —
e.g. ELITEA-0679's "using the default image model" with no model-selection step — the
`select_model()` call is a **test artifact**, and the repair is to **delete it**, not to
substitute today's model name. Substituting guarantees the same red the next time the
catalog moves.

Only keep a literal when the case *itself* names the model (then the assertion is the point,
e.g. `test_agent_llm_selector_openai_models.py`).

## Related live facts

- Model options carry dynamic testids: `model-selector-option-<slug>`
  (e.g. `model-selector-option-gpt-5-mini`); the composer's current model is
  `model-selector-name`. `ChatPage.select_model`'s raw `[role="menuitem"]` handle is
  pre-existing tech debt (#25/#42) that could migrate to the testid pattern.
- Switching the model **no longer resets** chat internal-tool toggles (Image Creation stayed
  `[checked]` across a switch). Old docstrings claiming an "enable after model switch to
  avoid reset" ordering are stale.
