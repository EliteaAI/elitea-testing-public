---
name: Dead-literal repair — check the case before substituting a new literal
description: A [FIX] card on a hardcoded literal that rotted is often a step the TMS case never asked for; delete it rather than re-point it
type: feedback
---

Pattern confirmed 2026-09-09 (ELITEA-0679 / card #2112, PR pending).

`test_create_image` failed at a 10s timeout on
`chat.select_model("GPT-5.2")` because `GPT-5.2` left the model catalog
(#2117). The obvious repair — swap in a model that currently exists — was
**wrong**: the TMS case names no model at all. Its precondition is *"at least
one shared image model is available as the default"* and its step says the
prompt is sent *"using the default image model"*. There was no model-selection
step in the case; the call was a pure test artifact.

**The move: read the case before choosing the replacement literal.**

- If the case NAMES the value → substituting the current one is correct.
- If the case says "the default" / says nothing → **delete the step.** The
  product's own default is then the oracle, and the test stops re-breaking on
  every catalog turnover. Any replacement literal just re-arms the same trap.

This generalises past model names to any rotting literal a test pins that the
case left unspecified: model display names, provider names, seeded entity
names, default project selections.

Related: `.agents/testing.md` § "LLM trigger-side flake" entries — display-name
literals are a recurring rot source here (see also the EL-6540 rename,
ELITEA-0501 / #2111, and `config.default_model_name = "gpt-5.2"` still dead at
`automation/config.py:235` under #2117).
