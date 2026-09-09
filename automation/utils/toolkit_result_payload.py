"""Parse a toolkit tool-run result payload out of the rendered result text.

Why this exists
---------------
``ToolkitTestSettingsPage.wait_for_tool_result()`` returns the *text content*
of the Run Results message item — the chat wrapper, the thought accordion, the
``✅ <tool> (0.192s)`` marker line, and then the tool's own result payload.

Until 2026-09-09 the spec for ELITEA-1866 pinned that payload as a **substring
of one serialization**::

    assert "{'total': 0, 'rows': []}" in result_text   # Python ``repr``

The product then started emitting the same result as **pretty-printed JSON**
(EliteaUI ``toolkits.helpers.js`` → ``prettifyToolkitMessage``: a tool message
that is *exactly* a JSON object is ``JSON.parse``d and re-emitted through
``JSON.stringify(parsed, null, 2)``; a Python-repr string is not valid JSON, so
that path used to be skipped). The **observable did not change** — the
just-created bucket is still empty — only its serialization did, so the
substring pin went red on a correct product (issue #2066).

Parsing the payload and comparing the parsed *structure* is
**strictly stronger** than the substring match it replaces (structural equality
on the whole payload vs. a substring match on one rendering of it) and it
survives a serialization change in **either** direction: JSON first, Python
``repr`` as the fallback, so the pre-drift form still parses.

Two properties of the live DOM shape this module (both captured live
2026-09-09, AFS § Adjustment 2026-09-09 § 2):

1. **There are no newlines in the text.** The payload renders inside a fenced
   ``<pre>``/``<code>`` block whose syntax highlighter emits one element per
   line with no newline text nodes, so ``text_content()`` collapses the block
   and each line's two-space indent survives as a run of spaces
   (``{   "total": 0,   "rows": [] }``). Any parsing that keys on ``\\n`` is
   wrong here.
2. **The chat wrapper prose precedes the payload**, and may itself contain
   braces. Splitting on the ``✅``/``❌`` marker — the same marker
   ``wait_for_tool_result`` polls on — drops that prose before the payload is
   searched for.

**This is observation, not substitution** (``.agents/testing.md`` § Fidelity
policy): every character parsed here was produced end to end by the real
system and merely read off the DOM. Nothing is routed, fulfilled or fabricated.

The function is pure and browser-free on purpose, so its behaviour is pinned by
``tests/unit/test_toolkit_result_payload.py`` against the shapes captured live.
"""

import ast
import json
import re
from typing import Any

#: The success/error marker ``wait_for_tool_result`` polls on. Everything
#: before the LAST one is chat wrapper prose, never the tool's result.
RESULT_MARKER_RE = re.compile(r"[✅❌]")

#: The result payload: the outermost ``{...}`` run that ends the text.
#: ``re.S`` so it still works if a future rendering does carry newlines.
RESULT_PAYLOAD_RE = re.compile(r"(\{.*\})\s*$", re.S)


def parse_tool_result_payload(result_text: str) -> Any:
    """Return the tool result payload parsed out of *result_text*.

    *result_text* is what
    :meth:`pages.toolkit_test_settings_page.ToolkitTestSettingsPage.wait_for_tool_result`
    returns — the whole rendered message item, not just the payload.

    JSON is tried first (the live 2026-09-09 rendering) and Python ``repr``
    second (the pre-drift rendering), so a serialization change in either
    direction keeps parsing.

    Raises:
        AssertionError: if no ``{...}`` payload follows the ``✅``/``❌``
            marker, or if what follows parses as neither JSON nor a Python
            literal. Both messages echo the raw text, because "the payload
            stopped rendering where it used to" is a real failure of the
            surface under test and must be loud — never a silent pass and
            never a skip.
    """
    tail = RESULT_MARKER_RE.split(result_text or "")[-1]
    match = RESULT_PAYLOAD_RE.search(tail)
    if match is None:
        raise AssertionError(
            "No result payload found after the ✅/❌ marker in: "
            f"{result_text!r}"
        )
    raw = match.group(1)
    try:
        return json.loads(raw)
    except ValueError:
        pass
    try:
        return ast.literal_eval(raw)
    except (ValueError, SyntaxError) as err:
        raise AssertionError(
            f"Result payload parsed as neither JSON nor a Python literal: "
            f"{raw!r} (from {result_text!r})"
        ) from err
