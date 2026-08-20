---
name: Toolkit-form Embedding Model console noise
description: Any Toolkit-type form (chat canvas or standalone) fires a persistent MUI "out-of-range value text-embedding-3-small" console warning in this local/DEV env — environmental, filter it.
type: feedback
---

Confirmed live (ELITEA-2081 session): as soon as ANY Toolkit type (e.g.
GitHub) is selected — chat-canvas `ToolkitEditor.jsx` or the standalone
`/toolkits/create` flow, same `ToolkitForm`/`ToolBase` machinery — the form's
"Embedding Model" MUI Select renders a hardcoded default value
(`"text-embedding-3-small"`) while its own options list is fetched
asynchronously. In THIS local/DEV environment the fetch never resolves to
include that value as a valid option (no embedding-model configuration
exists here) — even after the fetch settles, the available-values set is
only the MUI loading placeholder `__single_select_loading__`, never the
default. The warning re-fires on EVERY re-render of the mounted form (each
keystroke, every Discard/Save/close) for as long as the canvas stays open —
it is not a one-off, transient blip like the other known-noise patterns.

**Not caused by whatever the test does** — confirmed independent of
Discard/close/create. Any test that opens a Toolkit-type form, does several
UI actions, and asserts `console_messages == []` at the end WILL hit this
unless filtered. Add a 4th console filter alongside the existing three
(secrets-403, CategorySection #656, Vite stream-externalization):

```python
def _is_known_embedding_model_out_of_range_warning(msg) -> bool:
    return "out-of-range value" in msg.text and "text-embedding-3-small" in msg.text
```

Worked example: `test_close_toolkit_canvas_without_saving.py` (ELITEA-2081).
The pre-existing `test_create_toolkit_from_conversation.py` (ELITEA-2083)
does NOT have this filter yet — if it starts flaking on the console
assertion, this is the first thing to check.
