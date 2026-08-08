---
name: MUI multi-select center click hits chip delete icon at 3+ items
description: Selecting a 3rd/4th item in an Input/Output multi-select can silently fail — click near the right edge instead
type: feedback
---

Every pipeline node's Input/Output multi-select (LLM/MCP/Toolkit/Code/State
modifier — all built on the same `FlowEditorSelect.InputSelect`/`OutputSelect`
component) renders selected values as MUI `Chip`s inside the field, each with
its own delete ("x") icon. `LocatorDescriptor.click()` clicks the element's
bounding-box CENTER by default. With 0-2 chips selected this is safe (the
center falls on empty field background), but once **3+ chips** are present
they can fill enough of the field's width that the center point lands
directly on a chip's own delete icon instead — clicking there REMOVES that
chip instead of opening the dropdown. Confirmed live, ELITEA-2045: selecting
a 3rd/4th LLM-node Output variable via the default center click silently
failed to open the popover at all, chip count frozen at 2, no error thrown
(the click "succeeded" as far as Playwright is concerned — it just hit the
wrong sub-element).

**Fixed in `PipelineDetailPage.open_llm_node_output_select()`**: clicks near
the field's right edge (`position={"x": box["width"] - 12, "y": box["height"]
/ 2}`) instead of center — chips are left-aligned, so the right-edge/arrow-
icon area is never covered regardless of chip count. Backward-compatible;
re-confirmed the only other existing caller
(`test_pipeline_llm_node_system_task_chat_history_config.py`) still passes.

**This same collision risk exists on every sibling multi-select** that
shares `_select_multi_select_option_and_close()`/`select_open_listbox_option()`
(MCP Input/Output, Toolkit Input/Output, Code Input/Output, State modifier
Input/Output/Variables-to-clean) — none of those methods were fixed this
session (only the LLM Output one, since that's what ELITEA-2045 touched).
If a future case needs to select 3+ items in ANY of these, check whether the
sibling method still uses a plain center `.click()` and apply the same
right-edge-offset fix if it does — don't assume it's LLM-Output-only.
