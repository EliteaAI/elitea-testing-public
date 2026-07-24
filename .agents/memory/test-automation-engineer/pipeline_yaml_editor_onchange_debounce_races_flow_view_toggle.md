---
name: Pipeline YAML editor's onChange is debounced 30ms — switching to Flow view right after typing can race it
description: Editing pipeline YAML via CodeMirror keyboard input and immediately clicking the Flow/Yaml toggle can show the PRE-edit Flow-view edges, because EditorPanel.jsx's onSelectChatMode reads Redux yamlCode at click-time and useCodeMirror.hooks.js debounces notifyChange 30ms after the last keystroke. Fix: poll the Save button's own enabled state (driven by the same yamlCode diff) before switching views — a condition-based, no-sleep wait.
type: feedback
---

ELITEA-2028 (PR #1033): `test_yaml_edit_transition_syncs_flow_view_and_enables_save`
first run failed at the Flow-view edge assertion (`edge_exists("Code 1", "LLM
1")` → False) even though the immediately-preceding YAML-content re-read
(`get_yaml_content()`) already showed the edited `transition: LLM 1` line.
Debug dump of `.react-flow__edge` testids right after `switch_to_flow_view()`
showed BOTH edges still pointing at `EliteAPipelineEnd` — the Flow view had
not picked up the edit at all.

**Root cause (traced in `../EliteaUI/src`):**
- `EliteaUI/src/[fsd]/shared/lib/hooks/useCodeMirror.hooks.js::onInputHandler`
  debounces `notifyChange` (→ `setYamlCode` → Redux `state.pipeline.yamlCode`)
  by **30ms** after the last keystroke via `setTimeout`.
- `EliteaUI/src/pages/Pipelines/Components/EditorPanel.jsx::onSelectChatMode`
  (the Flow/Yaml toggle's onChange) reads `yamlCode` from its own `useCallback`
  closure — current as of the LAST RENDER before the click — and only calls
  `onParseCodeToJson(yamlCode)` (which recomputes the Flow-view node/edge
  layout) when switching TO Flow mode.
- If the toggle click fires before the 30ms debounce has flushed AND before
  React has re-rendered with the updated `yamlCode`-dependent closure, the
  Flow view re-parses the STALE (pre-edit) YAML string. A raw DOM read of the
  YAML editor's text content (e.g. `get_yaml_content()`) is unaffected by this
  — it reads the CodeMirror DOM directly, which updates on every keystroke,
  independent of the debounced Redux dispatch. That's why the YAML-content
  assertion passed while the Flow-view assertion failed on the exact same run.

**Fix, additive, in `PipelineDetailPage.edit_node_transition_in_yaml()`:**
after the `keyboard.type(new_line_text)` call, poll the Save button's own
`disabled` attribute via `page.wait_for_function("(el) => el && !el.disabled",
arg=self.save_button.element_handle())` before returning. The Save button's
enabled state is driven by the SAME Redux `yamlCode`-vs-initial diff
(`useIsPipelineYamlCodeDirty.js`), so it's a real condition-based signal that
the edit has landed — not a blind sleep, and not vulnerable to the debounce
window being longer/shorter than any fixed guess.

**Takeaway for any future case that edits pipeline YAML then immediately
switches to Flow view (or otherwise depends on the app's parsed-from-YAML
state):** never switch views / read derived state in the same "breath" as a
keyboard edit to this CodeMirror instance — always wait on an app-visible
signal driven by the same Redux slice first (Save-button state is the
cheapest one already exposed via an existing page-object method).

**Adjacent-PR conflict heads-up:** PR #1028 (ELITEA-2018, still OPEN at the
time of this note) independently touches `PipelineDetailPage.get_yaml_content()`
in the same file/area (adds a `.cm-line` fallback tier for a DIFFERENT race —
testid-tagging lag, see `get_yaml_content_codemirror_line_testid_race_and_cm_line_fallback.md`
on that branch). My PR #1033 inserts a NEW method
(`edit_node_transition_in_yaml`) immediately after `get_yaml_content()`'s
current body. Both changes are additive and compatible, but they sit close
enough in the file to produce a textual merge conflict at integration time —
resolve by keeping both (PR #1028's fallback tier stays inside
`get_yaml_content()`'s body; my new method stays appended after it).
