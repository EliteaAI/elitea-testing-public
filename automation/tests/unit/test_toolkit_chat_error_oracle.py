"""Pins the ELITEA-1140 / #1817 toolkit-chat error oracle against REAL payloads.

The repaired test (`tests/ui/toolkits/test_toolkit_parameterized.py::
TestChatWithToolkit::test_chat_with_toolkit`) used to judge a toolkit tool
execution by scanning the chat message for the substring ``"error"``. That guard
broke CI on a **successful** run (GHA ``32931571484``): the GitHub toolkit
returned this repository's own branch list, which contains
``tests/ELITEA-1980-credential-error-states`` and
``tests/ELITEA-2392-ai-providers-page-sections-load-without-error``. The scanned
text IS user data, so the guard was a race against our own branch names.

Deleting it was not enough either: on a genuine 401 the model still narrates
*"…when trying to list the **branches**…"*, which satisfies
``chat_response_keywords`` — removal alone would have converted a false-RED into
a silent false-GREEN. So the guards were replaced by a positive, anchored match
on the toolkit's own ``tool_output`` (``utils/toolkit_output``), and these tests
are what stop anyone reintroducing a substring scan.

**Every payload here was captured from the running system** — the failures from a
real GitHub 401 (expired PAT, issue #1673) and a real Confluence authorization
rejection, the successes from real ``list_branches_in_repo`` / ``list_projects``
/ ``list_pages_with_label`` calls — and is stored under ``data/``. Reading
recorded product output back is observation; authoring a payload would be
substitution (``.agents/testing.md`` § Fidelity policy).

One provenance nuance, so nobody re-litigates it while diffing against #1817:
the ``agent_tool_end`` samples are byte-verbatim wire frames, but **Sample A is
verbatim of ``last_msg.lower()``** — it is the chat text as the *old assertion
saw it*, lower-cased by the guard itself, which is why it reads in lower case
against #1817's mixed-case excerpt. It was matched against the CI log before
being stored. Full provenance for each sample is in the AFS:
``test-specs/toolkits/lfix_toolkit_chat_error_oracle_ELITEA-1140.md``.
"""

import json
from pathlib import Path

import pytest
from toolkit_configs import TOOLKIT_CONFIGS
from utils.toolkit_output import (
    find_tool_end_frames,
    get_tool_output,
    observed_frame_kinds,
    tool_output_matches_success,
)

_DATA = Path(__file__).parent / "data"

# The patterns UNDER TEST are the ones the suite actually ships — not copies —
# so a regression in the registry fails here.
GITHUB_PATTERN = TOOLKIT_CONFIGS["github"].tool_output_success_pattern
JIRA_PATTERN = TOOLKIT_CONFIGS["jira"].tool_output_success_pattern
CONFLUENCE_PATTERN = TOOLKIT_CONFIGS["confluence"].tool_output_success_pattern


def _frame(name: str) -> dict:
    return json.loads((_DATA / f"elitea1140_agent_tool_end_{name}.json").read_text())


# Sample A — the CI chat message that broke the old guard (GHA 32931571484,
# 2026-08-26). This is the CHAT channel, i.e. LLM narration, not tool_output.
SAMPLE_A_CHAT_MESSAGE = (
    _DATA / "elitea1140_github_branch_list_chat_message_ci.txt"
).read_text().strip()

# Sample B — real FAILURE: github `list_branches_in_repo` on the expired PAT
# (localhost, 2026-08-27). Sample C — real SUCCESS: jira `list_projects`.
# Sample D — real SUCCESS: github `list_branches_in_repo` via anonymous auth.
FRAME_B_GITHUB_401 = _frame("github_401_failure")
FRAME_C_JIRA_SUCCESS = _frame("jira_success")
FRAME_D_GITHUB_SUCCESS = _frame("github_success")

# Confluence, captured live 2026-08-27 against epamelitea.atlassian.net / space
# AT (all three real `list_pages_with_label` calls, nothing authored):
#   E — SUCCESS, empty: label 'test' (the SHIPPED label) matches zero pages
#       there today, so the shape CI will actually see is `[]`.
#   F — SUCCESS, non-empty: same tool, label 'test-automated', captured only to
#       learn the populated shape so the pattern's other branch is observed too.
#   G — FAILURE: a credential whose API key was corrupted, so Confluence really
#       rejected the request. Its shape is prose, and is NOT github's
#       "Failed to list branches: 401 …" — capture, never infer.
FRAME_E_CONFLUENCE_SUCCESS_EMPTY = _frame("confluence_success_empty")
FRAME_F_CONFLUENCE_SUCCESS = _frame("confluence_success")
FRAME_G_CONFLUENCE_AUTH_FAILURE = _frame("confluence_auth_failure")

SAMPLE_B_GITHUB_401 = get_tool_output(FRAME_B_GITHUB_401)
SAMPLE_C_JIRA_SUCCESS = get_tool_output(FRAME_C_JIRA_SUCCESS)
SAMPLE_D_GITHUB_SUCCESS = get_tool_output(FRAME_D_GITHUB_SUCCESS)
SAMPLE_E_CONFLUENCE_SUCCESS_EMPTY = get_tool_output(FRAME_E_CONFLUENCE_SUCCESS_EMPTY)
SAMPLE_F_CONFLUENCE_SUCCESS = get_tool_output(FRAME_F_CONFLUENCE_SUCCESS)
SAMPLE_G_CONFLUENCE_AUTH_FAILURE = get_tool_output(FRAME_G_CONFLUENCE_AUTH_FAILURE)


# ---------------------------------------------------------------------------
# THE card, in two assertions
# ---------------------------------------------------------------------------

def test_github_success_output_contains_the_word_error_and_is_still_a_success():
    """The real github SUCCESS payload contains ``error`` — and passes.

    This single pair IS card #1817: the substring scan is wrong on the wire
    channel too (the same branch names travel in ``tool_output``), and the
    anchored positive matcher is right. If anyone reintroduces a substring
    scan, this test is where it dies.
    """
    assert "error" in SAMPLE_D_GITHUB_SUCCESS, (
        "captured github success payload no longer contains 'error' — this "
        "test's premise depends on it; re-capture rather than relax it"
    )
    assert tool_output_matches_success(SAMPLE_D_GITHUB_SUCCESS, GITHUB_PATTERN) is True


def test_the_removed_substring_guard_misclassified_that_very_payload():
    """Documents the removed guard's behaviour on a legitimate success.

    ``assert "error" not in last_msg.lower()`` — the exact predicate deleted
    from Step 5 — evaluates False on BOTH channels of a healthy run: the chat
    message CI actually failed on, and the tool_output behind it.
    """
    assert "error" in SAMPLE_A_CHAT_MESSAGE.lower()      # chat channel  → old guard RED
    assert "error" in SAMPLE_D_GITHUB_SUCCESS.lower()    # wire channel  → same trap


# ---------------------------------------------------------------------------
# A real failure must still be caught
# ---------------------------------------------------------------------------

def test_real_github_401_is_classified_as_a_failure():
    assert SAMPLE_B_GITHUB_401.startswith("Failed to list branches: 401")
    assert tool_output_matches_success(SAMPLE_B_GITHUB_401, GITHUB_PATTERN) is False


def test_real_github_401_does_not_pass_any_other_toolkit_pattern():
    assert tool_output_matches_success(SAMPLE_B_GITHUB_401, JIRA_PATTERN) is False


# ---------------------------------------------------------------------------
# Patterns must not cross-match — a pattern loose enough to match another
# toolkit's payload is loose enough to re-admit the original bug
# ---------------------------------------------------------------------------

def test_jira_success_matches_only_the_jira_pattern():
    assert tool_output_matches_success(SAMPLE_C_JIRA_SUCCESS, JIRA_PATTERN) is True
    assert tool_output_matches_success(SAMPLE_C_JIRA_SUCCESS, GITHUB_PATTERN) is False


def test_github_success_does_not_match_the_jira_pattern():
    assert tool_output_matches_success(SAMPLE_D_GITHUB_SUCCESS, JIRA_PATTERN) is False


def test_patterns_are_anchored_at_the_start_of_the_output():
    """A success shape prefixed by anything else is NOT a success.

    Anchoring is what makes the matcher a statement about the tool's output
    rather than a substring hunt in the other direction.
    """
    assert tool_output_matches_success("Failed: " + SAMPLE_D_GITHUB_SUCCESS, GITHUB_PATTERN) is False
    assert tool_output_matches_success("Error. " + SAMPLE_C_JIRA_SUCCESS, JIRA_PATTERN) is False


# ---------------------------------------------------------------------------
# The empty-pattern fallback must never read as a pass
# ---------------------------------------------------------------------------

def test_empty_pattern_raises_instead_of_silently_passing():
    """Most TOOLKIT_CONFIGS entries have no captured success shape.

    Treating "" as a match would hand every one of them a free green.
    """
    with pytest.raises(ValueError):
        tool_output_matches_success(SAMPLE_D_GITHUB_SUCCESS, "")
    assert TOOLKIT_CONFIGS["gitlab"].tool_output_success_pattern == ""


# ---------------------------------------------------------------------------
# Frame selection — the Tier-1 half of the oracle
# ---------------------------------------------------------------------------

def test_finds_the_agent_tool_end_frame_for_the_expected_tool_and_toolkit():
    frames = [FRAME_B_GITHUB_401, FRAME_C_JIRA_SUCCESS, FRAME_D_GITHUB_SUCCESS]
    display_name = FRAME_D_GITHUB_SUCCESS["response_metadata"]["metadata"]["display_name"]

    found = find_tool_end_frames(
        frames, tool_name="list_branches_in_repo", toolkit_display_name=display_name
    )

    assert len(found) == 1
    assert get_tool_output(found[0]) == SAMPLE_D_GITHUB_SUCCESS


def test_another_toolkits_tool_call_is_not_accepted_as_evidence():
    """Two github frames differing only by toolkit: the display name decides."""
    frames = [FRAME_B_GITHUB_401, FRAME_D_GITHUB_SUCCESS]
    expired_name = FRAME_B_GITHUB_401["response_metadata"]["metadata"]["display_name"]

    found = find_tool_end_frames(
        frames, tool_name="list_branches_in_repo", toolkit_display_name=expired_name
    )

    assert len(found) == 1
    assert get_tool_output(found[0]) == SAMPLE_B_GITHUB_401


def test_a_tool_that_never_ran_yields_no_frames():
    """The hole Tier 1 closes: a model answering from memory calls nothing."""
    assert find_tool_end_frames([FRAME_C_JIRA_SUCCESS], tool_name="list_branches_in_repo") == []


def test_sent_frames_and_protocol_noise_are_ignored():
    echoed = dict(FRAME_D_GITHUB_SUCCESS, _direction="sent")
    noise = [None, "42[]", {"event": "chat_predict", "_direction": "received"}]

    assert find_tool_end_frames([echoed, *noise], tool_name="list_branches_in_repo") == []


def test_get_tool_output_returns_empty_string_for_a_frame_without_one():
    assert get_tool_output({"type": "agent_tool_end", "_direction": "received"}) == ""
    assert get_tool_output(None) == ""


# ---------------------------------------------------------------------------
# Confluence — the entry that could report GREEN on a failed call until now
# ---------------------------------------------------------------------------

def test_confluence_auth_failure_is_classified_as_a_failure():
    """The reason confluence needed a captured pattern at all.

    Before it had one, this payload sailed through every remaining tier: Tier 1
    passes (the frame exists, the output is non-empty), Tier 2 classified
    nothing, and Tier 3 passes because the model narrates the failure using all
    of ``["page", "list", "label"]`` — *"I ran into an error trying to list
    pages with the label 'test'"*. Net: GREEN on a broken toolkit.
    """
    assert SAMPLE_G_CONFLUENCE_AUTH_FAILURE.startswith("Tool execution error!")
    assert tool_output_matches_success(SAMPLE_G_CONFLUENCE_AUTH_FAILURE, CONFLUENCE_PATTERN) is False


def test_confluence_failure_shape_is_not_githubs_and_was_not_inferred():
    r"""Two toolkits, two unrelated failure shapes — hence capture-only.

    github fails with ``Failed to list branches: 401 …``; confluence fails with
    a prose block. A pattern reasoned from one toolkit's failure would have been
    wrong about the other, which is the same trap as the refuted
    ``^Branches in \S+:`` inference (AFS § Finding 4).
    """
    assert SAMPLE_B_GITHUB_401.startswith("Failed to list branches: 401")
    assert not SAMPLE_G_CONFLUENCE_AUTH_FAILURE.startswith("Failed to list")


def test_both_captured_confluence_success_branches_match():
    """Empty and populated results are both successes — both observed live.

    The shipped label ('test') matches zero pages in space AT today, so ``[]``
    is the shape CI sees; ``[{"id": …}]`` was captured with an existing label so
    the alternation's other branch rests on observation too, not on a guess
    about what a populated array looks like.
    """
    assert SAMPLE_E_CONFLUENCE_SUCCESS_EMPTY == "[]"
    assert SAMPLE_F_CONFLUENCE_SUCCESS.startswith('[{"id":')
    assert tool_output_matches_success(SAMPLE_E_CONFLUENCE_SUCCESS_EMPTY, CONFLUENCE_PATTERN) is True
    assert tool_output_matches_success(SAMPLE_F_CONFLUENCE_SUCCESS, CONFLUENCE_PATTERN) is True


def test_confluence_pattern_does_not_admit_the_other_toolkits_payloads():
    """Both are JSON arrays, so the anchor names confluence's observed key."""
    assert tool_output_matches_success(SAMPLE_D_GITHUB_SUCCESS, CONFLUENCE_PATTERN) is False
    assert tool_output_matches_success(SAMPLE_C_JIRA_SUCCESS, CONFLUENCE_PATTERN) is False
    assert tool_output_matches_success(SAMPLE_F_CONFLUENCE_SUCCESS, GITHUB_PATTERN) is False
    assert tool_output_matches_success(SAMPLE_F_CONFLUENCE_SUCCESS, JIRA_PATTERN) is False


def test_confluence_wire_tool_name_really_is_the_configured_indicator():
    """Tier 1 must be RIGHT, not accidentally right.

    ``test_tool_result_indicator`` is documented as "text expected in result",
    and Tier 1 matches it against ``response_metadata.tool_name``. For github
    and jira the two merely coincide. Confirmed for confluence by capture: the
    wire name IS ``list_pages_with_label``.
    """
    for frame in (
        FRAME_E_CONFLUENCE_SUCCESS_EMPTY,
        FRAME_F_CONFLUENCE_SUCCESS,
        FRAME_G_CONFLUENCE_AUTH_FAILURE,
    ):
        assert frame["response_metadata"]["tool_name"] == "list_pages_with_label"
    assert TOOLKIT_CONFIGS["confluence"].test_tool_result_indicator == "list_pages_with_label"


# ---------------------------------------------------------------------------
# The registry invariant that makes the gap impossible to reintroduce quietly
# ---------------------------------------------------------------------------

def test_every_toolkit_that_actually_runs_has_a_captured_success_shape():
    """A toolkit reaching the chat test must be classifiable, or say why not.

    This is the static half of the guarantee; ``pytest.skip`` in Step 5 is the
    runtime half. Confluence sat in exactly this hole — no ``skip_reason``,
    wired into three CI workflows, and no captured shape — so a failed tool
    call read as GREEN. Adding a toolkit now forces the choice explicitly:
    capture its ``tool_output``, or give it a ``skip_reason`` naming the gap.
    """
    unclassifiable = [
        key
        for key, cfg in TOOLKIT_CONFIGS.items()
        if not cfg.skip_reason and not cfg.tool_output_success_pattern
    ]
    assert unclassifiable == [], (
        f"{unclassifiable} run test_chat_with_toolkit but have no captured "
        f"tool_output_success_pattern, so a failed tool call cannot be told "
        f"from a successful one. Capture the shape live, or set skip_reason."
    )


def test_observed_frame_kinds_separates_a_harness_failure_from_a_missing_call():
    """Tier 1's message must not report three causes identically.

    ``0 of 0 frames`` is the collector (or the environment) failing; ``0 of
    many`` is the model never calling the tool. The pair is what tells them
    apart in a CI log nobody can re-run interactively.
    """
    assert observed_frame_kinds([]) == []
    assert observed_frame_kinds(None) == []

    kinds = observed_frame_kinds([FRAME_F_CONFLUENCE_SUCCESS, FRAME_C_JIRA_SUCCESS])
    assert ("agent_tool_end", "list_pages_with_label") in kinds
    assert ("agent_tool_end", "list_projects") in kinds
    assert kinds == sorted(kinds)

    # A frame with no payload `type` still identifies itself by event name,
    # and sent frames never count as observed evidence.
    assert observed_frame_kinds(
        [{"event": "chat_message_sync", "_direction": "received"}]
    ) == [("chat_message_sync", "")]
    assert observed_frame_kinds([dict(FRAME_F_CONFLUENCE_SUCCESS, _direction="sent")]) == []
