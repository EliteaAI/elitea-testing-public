---
name: LLM-selector target model must differ from the dedicated agent's creation-time model
description: When a test creates a dedicated agent via _build_dedicated_agent_payload() using settings.default_model_name AND then "switches" the LLM selector to a target model constant, the target must be verified distinct from settings.default_model_name's DISPLAY name or the switch/persistence assertions become vacuous (old == new, always passes).
type: feedback
---

## The bug class (caught in ELITEA-1880 review, fix round R1)

`settings.default_model_name` (`config.py`) is `"gpt-5.2"`, which renders in
the UI as the display name `"GPT-5.2"` (confirmed independently by
`test_import_agent_valid_md_file.py`'s `EXPECTED_MODEL_DISPLAY_NAME` and by
`test_agent_llm_selector_anthropic_models.py`'s use of the same constant for
agent creation). Any test that:

1. creates a dedicated agent with `model_name: settings.default_model_name`
   in its `_build_dedicated_agent_payload()`, AND
2. separately defines a `TARGET_MODEL_DISPLAY_NAME` constant to "switch to"
   via the UI and assert the switch/save/reload-persistence,

silently breaks if `TARGET_MODEL_DISPLAY_NAME` is ALSO `"GPT-5.2"` — the test
still runs green (Step 3/4's "new model shown" and the reload-persistence
step assert `get_selected_model_name() == TARGET_MODEL_DISPLAY_NAME`, which
is trivially true when nothing changed at all). This is a **vacuous-assertion
coverage gap invisible to**: the mechanical locator-policy grep, a single
green local run, AND the N×-hardening gate (it's deterministic, not flaky —
it just never tests the thing it claims to).

## The fix pattern

- Pick a target model that is a DIFFERENT display name from
  `settings.default_model_name`'s rendered form. For reasoning-capable-model
  cases specifically, `"GPT-5.4"` is confirmed live and stable (dynamic
  testid `model-selector-option-gpt-5.4`, per ELITEA-1880's AFS exploration).
- **Also add a defensive runtime guard**, not just a code comment — assert
  `TARGET_MODEL_DISPLAY_NAME != initial_model_name` right after reading the
  agent's actual starting model (Step 2's `get_selected_model_name()` call).
  A comment alone doesn't survive a future edit to either constant; the
  assertion fails loudly if the collision ever recurs (e.g. if
  `settings.default_model_name` is bumped to `"gpt-5.4"` later).

## Where to check this on any future LLM-selector test

Any test file with BOTH a `_build_dedicated_agent_payload()` using
`settings.default_model_name` AND a hardcoded `TARGET_MODEL_DISPLAY_NAME` /
similar "model to switch to" constant is a candidate for this bug class.
`test_agent_llm_selector_anthropic_models.py` (ELITEA-1881) is safe by
construction — its target models are the 3 Anthropic Claude variants, never
`"GPT-5.2"`.
