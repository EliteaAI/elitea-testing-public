---
name: GenerateEntityModalPageBase shared page-object pattern
description: Shared modal-shell page-object base for entity "Build with AI" generation flows (Agent/Skill/future entities) — reuse recipe and regression discipline for extending it
type: reference
---

`automation/pages/generate_entity_modal_page_base.py` (`GenerateEntityModalPageBase`)
holds the modal-shell mechanics shared by every entity's "Build with AI"
generation flow, all of which render the same `GenerateEntityModal.jsx` /
`GenerateEntityButton.jsx` presentation components in EliteaUI, distinguished
only by `entityLabel` ("agent", "skill", possibly "pipeline"/others later).

Extracted from `generate_agent_modal_page.py` (originally ELITEA-1915,
agent-only) while implementing ELITEA-2001 (skill sibling). Concrete
subclasses today: `GenerateAgentModalPage`, `GenerateSkillModalPage`.

## What the base owns

- `open_modal()`, `fill_prompt()`, `get_prompt_value()`, `is_generate_enabled()`
- `mock_generate_failure()` / `mock_generate_success()` / `clear_generate_mock()`
  — route-mock helpers keyed off `self.GENERATE_DRAFT_ROUTE`
- `expect_generate_response()` (context manager) / `click_generate_and_wait_for_response()`
- `is_error_alert_visible()`, `get_error_message()`
- `wait_for_loading_visible/hidden()`, `wait_for_review_form()`,
  `wait_for_input_step()` / `wait_for_input_step_hidden()`

## What a concrete subclass must supply

1. `GENERATE_DRAFT_ROUTE` — the entity-specific generate-draft endpoint glob
   (e.g. `**/elitea_core/generate_skill_draft/**`).
2. All 10 `LocatorDescriptor` fields (`open_button`, `modal`, `close_button`,
   `prompt_input`, `error_alert`, `loading_indicator`, `generate_button`,
   `cancel_button`, `back_button`, `approve_button`) with the entity's
   `generate-<entity>-*` testid naming convention.
3. `_is_generate_draft_url(self, url: str) -> bool` — precise match against
   the entity's own endpoint substring (used by `expect_generate_response()`
   to avoid matching a sibling entity's request if multiple modals were ever
   open in the same page, which doesn't happen today but keeps the base
   generic).

## Reuse recipe for a future third entity (e.g. Pipeline)

If a Pipeline (or any other) "Build with AI" flow ever gets its shared-component
props wired (mirroring the `generate-agent-*`/`generate-skill-*` convention with
`generate-pipeline-*`), do NOT write a new modal-shell page object from scratch://
subclass `GenerateEntityModalPageBase` exactly like `GenerateSkillModalPage`
does — only the route constant, the 10 locator testids, and
`_is_generate_draft_url()` need to be entity-specific.

## Regression discipline when touching the base

The base itself has (as of ELITEA-2001) 2 subclass callers. Any change to a
method body in `GenerateEntityModalPageBase` is a shared-caller-file change
per Hard Rule 3 — enumerate every subclass (`grep -rl "GenerateEntityModalPageBase" automation/pages/`)
and re-run each entity's build-with-ai spec locally before shipping. The
ELITEA-2001 extraction itself was NOT purely additive on
`generate_agent_modal_page.py` (method bodies moved out, not appended) —
verified via the shared-file regression protocol: enumerated the sole caller
(`test_agent_build_with_ai.py`), re-ran it green 2x post-refactor.
