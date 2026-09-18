"""Pins the ELITEA-1866 / #2066 tool-result payload parser against the shapes
that were captured live.

The repaired spec (``tests/ui/toolkits/
test_toolkit_creation_create_bucket_verify_list_files.py``, Step 31) used to
assert the tool result by matching the substring ``"{'total': 0, 'rows': []}"``
— a Python ``repr``. The product now renders the SAME empty result as
pretty-printed JSON (EliteaUI ``prettifyToolkitMessage``), so the pin went red
on a correct product. The substring match was replaced by
``parse_tool_result_payload(...) == {"total": 0, "rows": []}``, and these tests
are what stop the parser silently regressing in either direction.

**Every string below was captured from the running system** by the analyst on
2026-09-09 (AFS ``test-specs/artifacts/
l2_create-bucket-via-toolkit-verify-list-files_ELITEA-1866.md``
§ Adjustment 2026-09-09 § 2), or is the pre-drift form quoted from the GHA
failure log of #2066. Reading recorded product output back is observation;
the only authored string here is the *negative* control, which exists to prove
the comparison can fail.

The single most load-bearing property, and the reason a ``\n``-based parser
would be wrong: **the live text carries NO newlines.** The payload renders in a
fenced block whose highlighter emits one element per line with no newline text
nodes, so ``text_content()`` collapses it and each line's two-space indent
survives as a run of spaces.
"""

import pytest
from utils.toolkit_result_payload import parse_tool_result_payload

EMPTY_RESULT = {"total": 0, "rows": []}

#: Live capture, 2026-09-09 — pretty-printed JSON, collapsed to one line by
#: ``text_content()``. Verbatim from the AFS § Adjustment § 2 capture block.
LIVE_PRETTY_JSON = (
    "EliteatoMessageless than a minute agoThought for less than a second"
    'my-artifact-toolkit: list_files✅ list_files (0.192s) {   "total": 0,'
    '   "rows": [] }'
)

#: The pre-drift rendering, verbatim from the #2066 GHA failure log's own
#: quoting of the assertion that used to pass.
PRE_DRIFT_PYTHON_REPR = (
    "EliteatoMessageless than a minute agoThought for less than a second"
    "my-artifact-toolkit: list_files✅ list_files (0.463s) "
    "{'total': 0, 'rows': []}"
)

#: Same live shape, but with braces in the wrapper prose BEFORE the marker —
#: the marker split is what keeps them out of the payload match.
PROSE_BRACES_BEFORE_MARKER = (
    "EliteatoMessageThought for less than a second I will call "
    '{"tool": "list_files"} nowmy-artifact-toolkit: list_files'
    '✅ list_files (0.192s) {   "total": 0,   "rows": [] }'
)

#: Negative control — a NON-empty result. Authored on purpose: its job is to
#: prove the comparison still fails when the bucket is not empty.
NON_EMPTY_RESULT = (
    "EliteatoMessagemy-artifact-toolkit: list_files✅ list_files (0.192s) "
    '{   "total": 1,   "rows": [{ "name": "a.txt" }] }'
)


def test_live_pretty_printed_json_parses_to_the_empty_result():
    assert parse_tool_result_payload(LIVE_PRETTY_JSON) == EMPTY_RESULT


def test_pre_drift_python_repr_still_parses_to_the_empty_result():
    """The fallback is what makes the repair survive drift in EITHER
    direction — if ``prettifyToolkitMessage`` ever takes its ``catch`` path
    again, the spec must not go red for it."""
    assert parse_tool_result_payload(PRE_DRIFT_PYTHON_REPR) == EMPTY_RESULT


def test_braces_in_the_prose_before_the_marker_are_not_mistaken_for_the_payload():
    assert parse_tool_result_payload(PROSE_BRACES_BEFORE_MARKER) == EMPTY_RESULT


def test_a_non_empty_result_does_not_compare_equal_to_the_empty_result():
    """The assertion this parser feeds must still FAIL when the bucket the
    case just created is not empty — the whole point of Step 31."""
    payload = parse_tool_result_payload(NON_EMPTY_RESULT)
    assert payload != EMPTY_RESULT
    assert payload == {"total": 1, "rows": [{"name": "a.txt"}]}


def test_a_result_with_no_payload_fails_loudly_and_echoes_the_raw_text():
    """"No payload" is a real failure of the surface under test — the parser
    must never return a default that would let Step 31 pass."""
    raw = "EliteatoMessagemy-artifact-toolkit: list_files✅ list_files (0.192s)"
    with pytest.raises(AssertionError) as excinfo:
        parse_tool_result_payload(raw)
    assert "No result payload found" in str(excinfo.value)
    assert raw in str(excinfo.value)
