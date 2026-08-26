"""Unit tests for `is_successful_tool_run()` in
`tests.ui.toolkits.test_mcp_test_settings_view_run_history` (ELITEA-1940).

Regression coverage for the PR review finding that the spec asserted only
``TOOL_KEY in first_result`` after a tool run
(`test_mcp_test_settings_view_run_history.py:141` / `:164` before the fix).

Why that was green-but-wrong: `ToolkitTestSettingsPage.wait_for_tool_result()`
(`pages/toolkit_test_settings_page.py:441`) resolves on the `[✅❌]` regex —
success OR failure — and returns the message text either way. The result
summary itself is built by EliteaUI's `indexChat.helpers.js:250-264` as
``${status} `${tool}`${execTime}``, where `status` is `❌` when the tool action
is `error`/`cancelled` and `✅` otherwise. **Both shapes name the tool**, so a
substring check on the tool name passed on a completely failed run — the test
would have reported GREEN while the MCP tool errored, and Run History would
have been populated with a failed execution the later steps then asserted
against.

These tests pin the fix: the SUCCESS MARKER, not the tool name, is what
distinguishes the two. Each `_FAILED_*` sample below contains `TOOL_KEY`, so
each one passes the pre-fix check and must fail this one.
"""

import pytest

from tests.ui.toolkits.test_mcp_test_settings_view_run_history import (
    TOOL_KEY,
    is_successful_tool_run,
)

# A successful run, as rendered in the Test Settings panel and confirmed live
# (AFS § Test Steps 5: "✅ read_wiki_structure — confirmed live at 1.182s,
# followed by the real DeepWiki page list"). `text_content()` concatenates the
# markdown-rendered summary and body.
_SUCCESS_TEXT = (
    f"✅ {TOOL_KEY} (1.182s)Available pages for AsyncFuncAI/deepwiki-open:"
    "1 DeepWiki-Open Overview1.1 Getting Started1.2 Docker & CI/CD Deployment"
)

# The same run, failed: `indexChat.helpers.js` swaps the icon and keeps the
# tool name. This is the exact shape the old `TOOL_KEY in result` check let
# through.
_FAILED_TOOL_ACTION_TEXT = (
    f"❌ {TOOL_KEY} (0.412s)MCP error -32603: upstream request failed"
)

# `useToolkitChat.hooks.js:396` — the client-side execution-error message.
# Also names the tool.
_FAILED_EXECUTION_TEXT = (
    f'❌ Failed to execute tool "{TOOL_KEY}"'
    "Error: Network requestfailedPlease check your toolkit configuration and try again."
)

# `indexChat.helpers.js:316` — a general tool-testing error, tool named in the
# body by the parameter echo that precedes it.
_FAILED_TOOL_TESTING_TEXT = (
    f"❌ Error occurred during tool testing:Error: {TOOL_KEY} timed out"
)


def test_accepts_a_successful_run():
    """The ✅ summary for this tool is the only shape that counts as success."""
    assert is_successful_tool_run(_SUCCESS_TEXT) is True


@pytest.mark.parametrize(
    "failed_text",
    [
        pytest.param(_FAILED_TOOL_ACTION_TEXT, id="failed-tool-action"),
        pytest.param(_FAILED_EXECUTION_TEXT, id="failed-execution"),
        pytest.param(_FAILED_TOOL_TESTING_TEXT, id="failed-tool-testing"),
    ],
)
def test_rejects_failures_that_still_name_the_tool(failed_text):
    """Every failure shape names the tool — the pre-fix check passed on all of them."""
    assert TOOL_KEY in failed_text, (
        "Sample must reproduce the defect's precondition: the tool name IS present"
    )
    assert is_successful_tool_run(failed_text) is False


def test_rejects_a_partially_failed_run():
    """A summary joins one line per tool action — any ❌ line fails the whole run.

    Guards the "several actions, one of them failed" shape: a ✅ line for the
    tool is present, so a marker-only check would pass.
    """
    partial = f"✅ {TOOL_KEY} (0.9s)❌ read_wiki_contents (0.3s)MCP error -32603"
    assert is_successful_tool_run(partial) is False


def test_rejects_a_successful_run_of_a_DIFFERENT_tool():
    """The ✅ must belong to the tool this case executes, not any tool."""
    assert is_successful_tool_run("✅ ask_question (0.8s)Some other answer") is False


def test_rejects_an_empty_or_marker_less_result():
    """No marker at all (e.g. a still-running or blank panel) is not success."""
    assert is_successful_tool_run("") is False
    assert is_successful_tool_run(f"{TOOL_KEY} (1.0s)Available pages for x:") is False
