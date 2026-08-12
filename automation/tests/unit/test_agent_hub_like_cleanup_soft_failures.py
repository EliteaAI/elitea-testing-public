"""Unit tests for `_cleanup_soft_failures()` in
`tests.ui.agents.test_agent_hub_like_agent_list_view` (ELITEA-2354).

Regression coverage for PR fix-round-1 review finding: cleanup-unlike
verification (unlike-response 204 status, restored like-count-to-0, no new
unexpected console errors) was `logger.error()`-only, never asserted. A
failed cleanup could therefore leave the test GREEN while permanently
polluting the shared, cross-session like-count baseline that sibling cases
in the family depend on — the failure was invisible to the test result.
These tests pin the fix: each of the three cleanup-unlike observations must
independently produce a soft-failure message when it fails (routed into the
same `soft_failures`/`pytest.fail()` mechanism already used for the known
#1215 defect), and none of them fire when cleanup succeeds cleanly.
"""

from tests.ui.agents.test_agent_hub_like_agent_list_view import (
    _cleanup_soft_failures,
)


def test_clean_cleanup_produces_no_soft_failures():
    """All three observations succeeding must not raise any soft failure."""
    failures = _cleanup_soft_failures(
        unlike_status=204,
        like_count_restored=True,
        final_like_count=0,
        unexpected_unlike_errors=[],
    )
    assert failures == []


def test_non_204_unlike_status_produces_a_soft_failure():
    """A non-204 unlike response must be surfaced, not merely logged — this
    is exactly the case that previously passed silently."""
    failures = _cleanup_soft_failures(
        unlike_status=500,
        like_count_restored=True,
        final_like_count=0,
        unexpected_unlike_errors=[],
    )
    assert len(failures) == 1
    assert "500" in failures[0]
    assert "204" in failures[0]


def test_like_count_not_restored_produces_a_soft_failure():
    """If the like count never settles back to 0, the shared baseline is
    left polluted for sibling cases — this must be a soft failure, not a
    log line."""
    failures = _cleanup_soft_failures(
        unlike_status=204,
        like_count_restored=False,
        final_like_count=1,
        unexpected_unlike_errors=[],
    )
    assert len(failures) == 1
    assert "1" in failures[0]


def test_unexpected_console_errors_on_unlike_produce_a_soft_failure():
    """A genuinely new console error on the cleanup unlike click must be
    surfaced, not swallowed."""
    failures = _cleanup_soft_failures(
        unlike_status=204,
        like_count_restored=True,
        final_like_count=0,
        unexpected_unlike_errors=["TypeError: Cannot read properties of undefined"],
    )
    assert len(failures) == 1
    assert "TypeError" in failures[0]


def test_all_three_failures_are_reported_independently():
    """Multiple simultaneous cleanup failures must each produce their own
    message — none masks another."""
    failures = _cleanup_soft_failures(
        unlike_status=500,
        like_count_restored=False,
        final_like_count=1,
        unexpected_unlike_errors=["TypeError: Cannot read properties of undefined"],
    )
    assert len(failures) == 3
