"""Unit tests pinning ELITEA-2263's bucket-page wait — the fix for the
settings-w02 gate failure of
``test_bucket_retention_link_navigates_to_bucket``.

What went wrong
---------------
Step 5 asserted the bucket row visible on a flat 20 s element budget. The
failure's own aria snapshot showed the popup rendering the artifacts EMPTY state
("Buckets: 0 / No buckets created yet") — the bucket list had simply not arrived
yet. ``Artifacts.jsx`` renders that state for the whole in-flight window, because
the ``?bucket=`` deep-link selection can only resolve once ``allBuckets`` has
loaded, and in the DEV account's project 399 (1 049 buckets, ~205 KB) the list
call measured 10.5-12.7 s from the API client and 14.8-18.0 s end-to-end in a
fresh tab on an IDLE machine. The 20 s budget was therefore *below the fetch cost
alone* — it never measured rendering at all, and any load on the machine tipped
it red. The failure text ("Locator expected to be visible") matches none of
``pytest.ini``'s ``--only-rerun`` patterns, so the class never even got a rerun.

The fix, and what these tests pin
---------------------------------
1. The wait is now **condition-based** (Hard Rule 5): the spec registers a
   context-level ``expect_event("response", …)`` for the popup's OWN
   project-scoped bucket-LIST read *before* the click, and resolves it *before*
   asserting the bucket row. A magic number can no longer race a variable fetch.
2. The remaining budgets are sized above the measured cost, so a slow-but-healthy
   backend cannot be reported as a missing bucket.

Both halves are pinned here, because either one silently regressing restores the
original failure: dropping the gate (a "simplification") or trimming the budget
back toward 20 s (a "speed-up").
"""

import inspect

import pytest

from tests.ui.admin import test_notification_link_navigates_to_bucket as spec

#: The notification's project in the DEV account this case runs against.
PROJECT_ID = 399

#: Measured end-to-end cost of the popup's bucket-list read on an IDLE machine
#: (2026-08-26): 16.9 / 18.5 / 20.1 s. Any budget at or below this is a coin flip.
MEASURED_IDLE_COST_MS = 20_100


class TestBudgetsExceedTheMeasuredCost:
    """A budget below the measured cost is not a budget — it is a flake."""

    def test_popup_element_budget_is_above_the_measured_idle_cost(self):
        assert spec.POPUP_ELEMENT_TIMEOUT >= 60_000, (
            f"POPUP_ELEMENT_TIMEOUT is {spec.POPUP_ELEMENT_TIMEOUT} ms, but the popup's "
            f"bucket list measured {MEASURED_IDLE_COST_MS} ms end-to-end on an IDLE "
            "machine and grows with project 399's bucket count. The settings-w02 gate "
            "failure was exactly this: a 20 s budget that expired while the list call "
            "was still in flight, so the spec read the artifacts EMPTY state and "
            "reported a live bucket as missing."
        )

    def test_bucket_list_read_budget_is_above_the_measured_idle_cost(self):
        assert spec.BUCKET_LIST_READ_TIMEOUT >= 60_000, (
            f"BUCKET_LIST_READ_TIMEOUT is {spec.BUCKET_LIST_READ_TIMEOUT} ms — the "
            f"read it gates measured {MEASURED_IDLE_COST_MS} ms on an idle machine. "
            "The wait is condition-based, so an unused budget costs nothing and a "
            "tight one costs a red gate."
        )


class TestBucketListReadMatcher:
    """The gate must fire on the LIST read of the RIGHT project, and nothing else."""

    @pytest.mark.parametrize(
        "url",
        [
            "http://localhost:5173/api/v2/artifacts/artifacts/s3/?project_id=399&format=json",
            "http://localhost:5173/api/v2/artifacts/artifacts/s3/?format=json&project_id=399",
            "http://localhost:5173/api/v2/artifacts/artifacts/s3/?project_id=399",
        ],
        ids=["list-pid-first", "list-pid-last", "list-pid-only"],
    )
    def test_matches_the_projects_own_bucket_list_read(self, url):
        assert spec._bucket_list_read_matcher(PROJECT_ID).search(url) is not None

    @pytest.mark.parametrize(
        "url",
        [
            # The per-bucket CONTENTS read — a different, LATER call. Gating on it
            # would defeat the fix: it cannot land before the list it depends on.
            "http://localhost:5173/api/v2/artifacts/artifacts/s3/"
            "autotest-1816-182606?project_id=399&format=json",
            # Another project's list — a same-named bucket elsewhere must not
            # satisfy this case's project-scoped gate.
            "http://localhost:5173/api/v2/artifacts/artifacts/s3/?project_id=406&format=json",
            # Prefix collisions on the project id, both directions.
            "http://localhost:5173/api/v2/artifacts/artifacts/s3/?project_id=3990&format=json",
            "http://localhost:5173/api/v2/artifacts/artifacts/s3/?project_id=1399&format=json",
            # A different param that merely ENDS in the gated name.
            "http://localhost:5173/api/v2/artifacts/artifacts/s3/"
            "?bucket_project_id=399&format=json",
            # Vite's own module URLs contain "/artifacts/" but are not REST reads.
            "http://localhost:5173/src/pages/Artifacts/Artifacts.jsx?t=1",
        ],
        ids=[
            "bucket-contents-read",
            "other-project-list",
            "pid-suffix-collision",
            "pid-prefix-collision",
            "param-name-collision",
            "vite-module",
        ],
    )
    def test_does_not_match_anything_else(self, url):
        assert spec._bucket_list_read_matcher(PROJECT_ID).search(url) is None

    def test_accepts_a_string_project_id(self):
        """``row["project_id"]`` arrives as an int, page objects pass strings —
        the matcher must not care which."""
        url = "http://localhost:5173/api/v2/artifacts/artifacts/s3/?project_id=399&format=json"
        assert spec._bucket_list_read_matcher("399").search(url) is not None


@pytest.fixture(scope="module")
def source() -> str:
    """The spec's test body, read from the module under pin."""
    return inspect.getsource(
        spec.TestNotificationBucketRetentionLinkNavigation
        .test_bucket_retention_link_navigates_to_bucket
    )


class TestStepFiveIsGatedOnTheResponse:
    """Structural pin: the wait must stay condition-based, in the right order."""

    def test_registers_the_response_gate_before_clicking_the_link(self, source):
        """Registered AFTER the click, the event can be missed entirely — the
        popup's list read may land before the listener exists."""
        gate = source.index('expect_event(\n                "response"')
        click = source.index("click_message_link_expecting_popup(")
        assert gate < click, (
            "The bucket-list response gate must be registered BEFORE the click that "
            "opens the popup; registering it afterwards races the very response it "
            "is meant to wait for."
        )

    def test_resolves_the_gate_before_asserting_the_bucket_row(self, source):
        """This is the fix. Asserting the row first is the original defect: the
        artifacts empty state renders for the whole in-flight window."""
        resolve = source.index("bucket_list_read.value")
        row_assertion = source.index("popup_artifacts.bucket_row(")
        assert resolve < row_assertion, (
            "Step 5 must wait for the popup's bucket-list read to LAND before "
            "asserting the bucket row, otherwise it asserts against the artifacts "
            "EMPTY state and reports a live bucket as missing."
        )

    def test_gate_uses_the_named_budget(self, source):
        assert "timeout=BUCKET_LIST_READ_TIMEOUT" in source

    def test_no_sleep_was_introduced(self, source):
        """Hard Rule 5 — the fix for a timing failure is never a sleep."""
        for banned in ("wait_for_timeout", "time.sleep", "sleep("):
            assert banned not in source, f"{banned} must not appear in this spec"
