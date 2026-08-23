"""UI Test for ELITEA-1810 — Create an Artifact Bucket via the Folder Icon
and Verify Retention-Policy Edit and Persistence.

Regression test for the whole retention-policy axis of the bucket form, which
no existing spec touches: sibling ELITEA-1808/1809/1817 all drive the same
``/artifacts/create-bucket`` form but leave Retention at its ``Years / 1``
default. This test creates a bucket with a NON-default policy, edits that
policy through the bucket dot-menu's "Rename" entry point, and proves the
edited value survives a save + reopen while a Cancel does not overwrite it.

Test flow (27 case steps, 1:1 with the AFS's Test Steps):
1.  Navigate to Artifacts.
2.  Click the create-bucket folder icon — full page nav to
    ``/artifacts/create-bucket``, not a modal.
3.  Verify the "New Bucket" form and its defaults (name ``new-bucket``,
    measure ``Years``, value ``1``, Save + Cancel present).
4.  Enter a generated unique bucket name.
5-7.  Open the retention dropdown (4 measures offered), select Months, set 10.
8.  Save — bucket-creation POST returns 200.
9-10. Verify the bucket is listed and record its list index.
11-12. Hover the row, open the dot-menu, click "Rename" — the edit form opens.
13. Verify the retention reads back as ``10 Months``. **SANCTIONED RED** —
    the product reopens it as ``304 Days`` (#1677); soft-asserted so the rest
    of the case still runs and this flips green when the product is fixed.
14-16. Select Weeks, set 20, Save — the bucket-update PUT returns 200.
17. Verify the bucket keeps the same name AND the same list index.
18-20. Reopen the edit form — retention persisted as ``20 Weeks`` (HARD
    assertion; this is the case's central claim and it holds live).
21-23. Select Days, set 1, click Cancel — verify NO bucket PUT fired.
24-27. Back at the list, reopen the edit form — retention is STILL
    ``20 Weeks``, i.e. Cancel did not overwrite the saved policy.

Case-text divergences asserted as the LIVE contract (reverse-masking guard):
- Steps 12/19/26 say "Edit"; the live dot-menu item is "Rename"
  (tracked CLARIFICATION #666/#650 — commented, not re-filed).
- The case's literal bucket name ``bucket-2`` is a placeholder, same
  established convention as ELITEA-1808/1832/1839 — a unique name is
  generated per run (an earlier run's leaked ``autotest-1810-b2-2251``
  bucket was found in the project during analysis).
- "Path 2 / second path": live there is exactly ONE bucket-creation entry
  point (``BucketHeader.jsx``'s single ``NewFolder``-icon button), which
  ELITEA-1808 drives too. The cases stay distinct because everything from
  step 11 on (retention edit / persistence / Cancel) is unique to this one.
  Left to the lead as a possible case-text clarification.

Known defect (sanctioned-RED, `.agents/testing.md` § Merge gate):
    #1677 — a Months retention policy reopens as Days (10 Months -> 304
    Days, 3 Months -> 92 Days). The backend stores calendar-accurate days
    and ``convertDaysToMeasure()`` (``src/utils/retentionPolicy.js``) only
    rebuilds "months" when ``days % 30 === 0``, unreachable for a real month
    policy. Deterministic, single-cause, isolated to Test Step 13; Weeks
    (x7) and Years (x365) round-trip cleanly. This spec's gate signature is
    exactly ONE soft failure, at Test Step 13.

Fidelity: no substitution of any kind. Every asserted value is produced by
the running system — the bucket is created and edited through the real UI,
and the two save assertions read the real POST/PUT responses.

AFS: test-specs/artifacts/l2_create-bucket-via-folder-icon-retention-edit-persistence_ELITEA-1810.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p1: high priority (matches case priority "high" / AFS l2)

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_bucket_retention_edit_persistence.py -v
"""

import logging
import time

import allure
import pytest
from playwright.sync_api import expect

from pages.artifacts_page import ArtifactsPage

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.regression,
    pytest.mark.new,
]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000        # fields, buttons, menus, rows
NAVIGATION_TIMEOUT = 15_000        # SPA route transitions, bucket-list refetch
SAVE_RESPONSE_TIMEOUT = 20_000     # bucket create POST / update PUT
# The project under test carries ~970 buckets, and the left panel refetches the
# WHOLE list after a bucket save. Measured live: the post-save refetch can take
# well over the 15s NAVIGATION_TIMEOUT the smaller sibling specs use, so the
# bucket-list waits get their own, larger condition-wait budget. Still a
# condition wait on the row's own testid — never a sleep.
BUCKET_LIST_TIMEOUT = 45_000

# ---------------------------------------------------------------------------
# Test data (from the case's own Test Data table, used verbatim live)
# ---------------------------------------------------------------------------
# Fresh-form defaults, confirmed live (CreateBucket.jsx — RETENTION_MEASURES[3]
# + DEFAULT_RETENTION_VALUE).
DEFAULT_BUCKET_NAME = "new-bucket"
DEFAULT_RETENTION_MEASURE = "Years"
DEFAULT_RETENTION_VALUE = "1"

# The four retention measures the SingleSelect offers. Keys are the option
# VALUES (as they appear in the `select-option-{value}` testid); values are
# the rendered, capitalized labels.
RETENTION_MEASURES = {
    "days": "Days",
    "weeks": "Weeks",
    "months": "Months",
    "years": "Years",
}

# Case Test Data — initial retention "10 Months".
CREATE_MEASURE = "months"
CREATE_VALUE = "10"

# Case Test Data — updated retention "20 Weeks" (the persisted end state).
EDIT_MEASURE = "weeks"
EDIT_VALUE = "20"

# Case Test Data — "1 Days (should not be saved)" via Cancel.
CANCEL_MEASURE = "days"
CANCEL_VALUE = "1"

EDIT_FORM_HEADING = "Edit bucket"
NEW_FORM_HEADING = "New Bucket"

# The bucket-update request the form fires on an edit save. Cancel must fire
# NONE of these — Test Step 23's "closes without saving".
BUCKET_REQUEST_SUBSTRING = "artifacts/buckets"


@allure.epic("Artifacts")
@allure.feature("Bucket Creation + Retention Policy")
class TestArtifactBucketRetentionEditPersistence:
    """ELITEA-1810 — Create a bucket with a custom retention policy, edit it,
    and verify persistence across save/reopen and non-persistence on Cancel.

    The bucket is created BY the test itself (case Test Steps 2-8 ARE the
    creation), so the ``artifact_bucket`` API fixture is deliberately NOT
    used — seeding via the API would substitute the very subject under test
    (`.agents/testing.md` § Fidelity policy). Teardown deletes the bucket
    through the UI path confirmed working during analysis, with the API
    client as a fallback (`ArtifactAPI.delete_bucket()` is known to 404 in
    this environment, #636).
    """

    @staticmethod
    def _delete_bucket_via_ui(artifacts_page: ArtifactsPage, bucket_name: str) -> None:
        """Delete a bucket through the UI dot-menu (teardown helper).

        Suite-local helper, not a page-object method: it is pure teardown
        composition over existing page-object methods, exercised by no
        assertion in this case.
        """
        artifacts_page.navigate_to_artifacts()
        artifacts_page.wait_for_bucket_in_list(bucket_name, timeout=NAVIGATION_TIMEOUT)
        artifacts_page.open_bucket_menu(bucket_name, timeout=UI_ELEMENT_TIMEOUT)
        artifacts_page.click_bucket_menu_delete_item(timeout=UI_ELEMENT_TIMEOUT)
        artifacts_page.delete_confirm_button.click()
        artifacts_page.wait_for_bucket_removed_from_list(
            bucket_name, timeout=BUCKET_LIST_TIMEOUT
        )

    @pytest.mark.p1
    @allure.title(
        "Create a bucket via the folder icon with a custom retention policy, "
        "edit the policy, and verify it persists across save/reopen while "
        "Cancel does not overwrite it"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1810_create-artifact-bucket-via-folder-icon-retention-policy.md",
        "onetest-ai Test Case link",
    )
    def test_bucket_retention_edit_and_persistence(self, page, artifact_api):
        """Drive the case's 27 steps end-to-end against the live system."""
        bucket_name = f"autotest-1810-{int(time.time())}"

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        artifacts_page = ArtifactsPage(page)
        bucket_created = False

        try:
            with allure.step("Step 1 — Navigate to the Artifacts section"):
                artifacts_page.navigate_to_artifacts()
                expect(artifacts_page.buckets_heading).to_be_visible(
                    timeout=NAVIGATION_TIMEOUT
                )

            with allure.step(
                "Step 2 — Click the create-bucket folder icon above the bucket "
                "list — verify it opens the 'New Bucket' form as a full page "
                "navigation, not a modal"
            ):
                artifacts_page.click_create_bucket_button(timeout=NAVIGATION_TIMEOUT)
                assert "/artifacts/create-bucket" in page.url, (
                    f"Expected URL to contain '/artifacts/create-bucket', "
                    f"got: {page.url!r}"
                )

            with allure.step(
                "Step 3 — Verify the 'New Bucket' form shows the Name field, "
                "the Retention policy section (measure + value) at their "
                "defaults, and BOTH the Save and Cancel buttons"
            ):
                assert (
                    artifacts_page.get_bucket_form_heading_text(
                        timeout=UI_ELEMENT_TIMEOUT
                    )
                    == NEW_FORM_HEADING
                ), "A fresh form load should be headed 'New Bucket', not the edit form"
                expect(artifacts_page.bucket_name_input).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                assert (
                    artifacts_page.bucket_name_input.input_value() == DEFAULT_BUCKET_NAME
                ), (
                    f"Name field should be pre-filled with the literal default "
                    f"{DEFAULT_BUCKET_NAME!r} on a fresh form load"
                )
                expect(artifacts_page.bucket_retention_measure_combobox).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                assert (
                    artifacts_page.get_retention_measure_text()
                    == DEFAULT_RETENTION_MEASURE
                ), (
                    f"Retention measure should default to "
                    f"{DEFAULT_RETENTION_MEASURE!r}, got "
                    f"{artifacts_page.get_retention_measure_text()!r}"
                )
                expect(artifacts_page.bucket_retention_value_input).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                assert (
                    artifacts_page.get_retention_value() == DEFAULT_RETENTION_VALUE
                ), (
                    f"Retention value should default to {DEFAULT_RETENTION_VALUE!r}, "
                    f"got {artifacts_page.get_retention_value()!r}"
                )
                expect(artifacts_page.bucket_save_button).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                # Step 23 depends on Cancel existing — asserting it here makes a
                # missing control fail early, with a clear message (AFS Axis 2).
                expect(artifacts_page.bucket_cancel_button).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                f"Step 4 — Enter the bucket name {bucket_name!r} (the case's "
                "literal 'bucket-2' is a placeholder — a unique name is "
                "generated per run)"
            ):
                artifacts_page.fill_bucket_name(bucket_name)
                assert artifacts_page.bucket_name_input.input_value() == bucket_name, (
                    f"Name field should show {bucket_name!r}, got "
                    f"{artifacts_page.bucket_name_input.input_value()!r}"
                )

            with allure.step(
                "Step 5 — Click the Retention policy dropdown (default 'Years') "
                "— verify it opens with all four retention measures"
            ):
                artifacts_page.open_retention_measure_dropdown(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                for measure_value, measure_label in RETENTION_MEASURES.items():
                    assert artifacts_page.is_retention_measure_option_visible(
                        measure_value
                    ), f"Retention option {measure_label!r} should be offered"
                    assert (
                        artifacts_page.get_retention_measure_option_text(measure_value)
                        == measure_label
                    ), (
                        f"Retention option {measure_value!r} should be labelled "
                        f"{measure_label!r}, got "
                        f"{artifacts_page.get_retention_measure_option_text(measure_value)!r}"
                    )

            with allure.step("Step 6 — Select 'Months' from the dropdown"):
                artifacts_page.select_retention_measure(
                    CREATE_MEASURE, timeout=UI_ELEMENT_TIMEOUT
                )
                assert (
                    artifacts_page.get_retention_measure_text()
                    == RETENTION_MEASURES[CREATE_MEASURE]
                ), (
                    f"Retention measure should now read "
                    f"{RETENTION_MEASURES[CREATE_MEASURE]!r}, got "
                    f"{artifacts_page.get_retention_measure_text()!r}"
                )

            with allure.step(
                f"Step 7 — Change the retention numerical value to {CREATE_VALUE!r}"
            ):
                artifacts_page.set_retention_value(CREATE_VALUE)
                assert artifacts_page.get_retention_value() == CREATE_VALUE, (
                    f"Retention value field should show {CREATE_VALUE!r}, got "
                    f"{artifacts_page.get_retention_value()!r}"
                )

            with allure.step(
                "Step 8 — Click Save — verify the bucket-creation POST returns "
                "200 (there is no toast on bucket save; the response is the "
                "only honest oracle)"
            ):
                create_response = artifacts_page.click_bucket_save_button(
                    timeout=SAVE_RESPONSE_TIMEOUT
                )
                bucket_created = True
                assert create_response.status == 200, (
                    f"Bucket creation POST should return 200, got "
                    f"{create_response.status} for {create_response.url}"
                )

            with allure.step(
                f"Step 9 — Verify bucket {bucket_name!r} appears in the bucket "
                "list — condition wait on its own dynamic row testid"
            ):
                artifacts_page.wait_for_bucket_in_list(
                    bucket_name, timeout=BUCKET_LIST_TIMEOUT
                )
                assert artifacts_page.count_bucket_rows(bucket_name) == 1, (
                    f"Expected exactly one {bucket_name!r} row in the bucket list"
                )

            with allure.step(
                "Step 10 — Note the bucket name and position in the bucket "
                "list (the UI exposes no bucket ID anywhere in the DOM — the "
                "list index is the only observable half of this step)"
            ):
                position_after_create = artifacts_page.get_bucket_row_index(bucket_name)
                allure.attach(
                    f"{bucket_name} -> index {position_after_create}",
                    name="Bucket position after create",
                    attachment_type=allure.attachment_type.TEXT,
                )

            with allure.step(
                "Step 11 — Hover the bucket row and click its 3-dot ellipsis "
                "menu — verify the dropdown appears"
            ):
                artifacts_page.open_bucket_menu(bucket_name, timeout=UI_ELEMENT_TIMEOUT)
                expect(
                    artifacts_page.bucket_menu_container(bucket_name)
                ).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(artifacts_page.bucket_menu_rename_menuitem).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 12 — Select the edit entry from the dropdown — LIVE label "
                "is 'Rename', not the case's 'Edit' (CLARIFICATION #666/#650; "
                "reverse-masking guard — assert the product's live contract) — "
                "verify the edit form opens"
            ):
                artifacts_page.click_bucket_menu_rename_item(
                    timeout=NAVIGATION_TIMEOUT
                )
                assert "/artifacts/create-bucket" in page.url, (
                    f"Rename should navigate to the bucket form route, got "
                    f"{page.url!r}"
                )
                assert (
                    artifacts_page.get_bucket_form_heading_text(
                        timeout=UI_ELEMENT_TIMEOUT
                    )
                    == EDIT_FORM_HEADING
                ), (
                    f"The form should be headed {EDIT_FORM_HEADING!r} when reached "
                    "via Rename (the same route serves create and edit)"
                )
                assert artifacts_page.bucket_name_input.input_value() == bucket_name, (
                    f"The edit form's Name field should be pre-loaded with "
                    f"{bucket_name!r}, got "
                    f"{artifacts_page.bucket_name_input.input_value()!r}"
                )

            with allure.step(
                f"Step 13 — Verify the retention policy reads back as "
                f"'{CREATE_VALUE} {RETENTION_MEASURES[CREATE_MEASURE]}' "
                "(SANCTIONED RED — Known defect: #1677, the product reopens a "
                "Months policy as '304 Days')"
            ):
                # Known defect: #1677 — a Months retention policy reopens as
                # Days (10 Months -> 304 Days). The backend stores
                # calendar-accurate days and convertDaysToMeasure() only
                # rebuilds "months" when days % 30 === 0, which a real month
                # policy never satisfies. Deterministic, single-cause,
                # isolated to this step. Asserted SOFT so the rest of the case
                # still runs and this flips green when the product is fixed —
                # deliberately NOT weakened to the buggy value.
                expect.soft(
                    artifacts_page.bucket_retention_measure_combobox
                ).to_have_text(
                    RETENTION_MEASURES[CREATE_MEASURE], timeout=UI_ELEMENT_TIMEOUT
                )
                expect.soft(artifacts_page.bucket_retention_value_input).to_have_value(
                    CREATE_VALUE, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 14 — Click the Retention policy dropdown and select 'Weeks'"
            ):
                artifacts_page.select_retention_measure(
                    EDIT_MEASURE, timeout=UI_ELEMENT_TIMEOUT
                )
                assert (
                    artifacts_page.get_retention_measure_text()
                    == RETENTION_MEASURES[EDIT_MEASURE]
                ), (
                    f"Retention measure should now read "
                    f"{RETENTION_MEASURES[EDIT_MEASURE]!r}, got "
                    f"{artifacts_page.get_retention_measure_text()!r}"
                )

            with allure.step(
                f"Step 15 — Change the numerical value to {EDIT_VALUE!r}"
            ):
                artifacts_page.set_retention_value(EDIT_VALUE)
                assert artifacts_page.get_retention_value() == EDIT_VALUE, (
                    f"Retention value field should show {EDIT_VALUE!r}, got "
                    f"{artifacts_page.get_retention_value()!r}"
                )

            with allure.step(
                "Step 16 — Click Save — an EDIT save is a PUT (not the create "
                "flow's POST); verify it returns 200"
            ):
                update_response = artifacts_page.click_bucket_save_button_expect_put(
                    timeout=SAVE_RESPONSE_TIMEOUT
                )
                assert update_response.status == 200, (
                    f"Bucket update PUT should return 200, got "
                    f"{update_response.status} for {update_response.url}"
                )

            with allure.step(
                "Step 17 — Verify the bucket is still listed under the same "
                "name AND at the same position as recorded in Step 10"
            ):
                artifacts_page.wait_for_bucket_in_list(
                    bucket_name, timeout=BUCKET_LIST_TIMEOUT
                )
                position_after_edit = artifacts_page.get_bucket_row_index(bucket_name)
                assert position_after_edit == position_after_create, (
                    f"Bucket {bucket_name!r} should keep its list position after "
                    f"a retention edit — was index {position_after_create}, now "
                    f"{position_after_edit}"
                )

            with allure.step(
                "Step 18 — Hover the bucket row and open its 3-dot menu again"
            ):
                artifacts_page.open_bucket_menu(bucket_name, timeout=UI_ELEMENT_TIMEOUT)
                expect(
                    artifacts_page.bucket_menu_container(bucket_name)
                ).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 19 — Select 'Rename' — the edit form opens"):
                artifacts_page.click_bucket_menu_rename_item(
                    timeout=NAVIGATION_TIMEOUT
                )
                assert (
                    artifacts_page.get_bucket_form_heading_text(
                        timeout=UI_ELEMENT_TIMEOUT
                    )
                    == EDIT_FORM_HEADING
                ), f"The form should be headed {EDIT_FORM_HEADING!r}"

            with allure.step(
                f"Step 20 — Verify the retention policy is now "
                f"'{EDIT_VALUE} {RETENTION_MEASURES[EDIT_MEASURE]}' — the save "
                "persisted (the case's central claim; HARD assertion)"
            ):
                expect(
                    artifacts_page.bucket_retention_measure_combobox
                ).to_have_text(
                    RETENTION_MEASURES[EDIT_MEASURE], timeout=UI_ELEMENT_TIMEOUT
                )
                expect(artifacts_page.bucket_retention_value_input).to_have_value(
                    EDIT_VALUE, timeout=UI_ELEMENT_TIMEOUT
                )

            # Arm the bucket-PUT listener BEFORE touching the form, so Step 23's
            # "closes without saving" is proven by the ABSENCE of the request
            # itself rather than inferred later from Step 27 (AFS Axis 2 — it
            # localises a Cancel regression to Step 23).
            cancel_puts = artifacts_page.capture_requests_matching(
                BUCKET_REQUEST_SUBSTRING, method="PUT"
            )
            try:
                with allure.step(
                    "Step 21 — Click the Retention policy dropdown and select 'Days'"
                ):
                    artifacts_page.select_retention_measure(
                        CANCEL_MEASURE, timeout=UI_ELEMENT_TIMEOUT
                    )
                    assert (
                        artifacts_page.get_retention_measure_text()
                        == RETENTION_MEASURES[CANCEL_MEASURE]
                    ), (
                        f"Retention measure should now read "
                        f"{RETENTION_MEASURES[CANCEL_MEASURE]!r}, got "
                        f"{artifacts_page.get_retention_measure_text()!r}"
                    )

                with allure.step(
                    f"Step 22 — Set the numerical value to {CANCEL_VALUE!r}"
                ):
                    artifacts_page.set_retention_value(CANCEL_VALUE)
                    assert artifacts_page.get_retention_value() == CANCEL_VALUE, (
                        f"Retention value field should show {CANCEL_VALUE!r}, got "
                        f"{artifacts_page.get_retention_value()!r}"
                    )

                with allure.step(
                    "Step 23 — Click Cancel — verify the edit form closes and "
                    "NO bucket-update PUT fired"
                ):
                    artifacts_page.click_bucket_cancel_button(
                        timeout=NAVIGATION_TIMEOUT
                    )
                    assert list(cancel_puts) == [], (
                        "Cancel must not save: expected no bucket PUT request, "
                        f"but captured {list(cancel_puts)!r}"
                    )
            finally:
                cancel_puts.stop()

            with allure.step("Step 24 — Verify the bucket list is visible again"):
                artifacts_page.wait_for_bucket_in_list(
                    bucket_name, timeout=BUCKET_LIST_TIMEOUT
                )

            with allure.step(
                "Step 25 — Hover the bucket row and open its 3-dot menu"
            ):
                artifacts_page.open_bucket_menu(bucket_name, timeout=UI_ELEMENT_TIMEOUT)
                expect(
                    artifacts_page.bucket_menu_container(bucket_name)
                ).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 26 — Select 'Rename' — the edit form opens"):
                artifacts_page.click_bucket_menu_rename_item(
                    timeout=NAVIGATION_TIMEOUT
                )
                assert (
                    artifacts_page.get_bucket_form_heading_text(
                        timeout=UI_ELEMENT_TIMEOUT
                    )
                    == EDIT_FORM_HEADING
                ), f"The form should be headed {EDIT_FORM_HEADING!r}"

            with allure.step(
                f"Step 27 — Verify the retention policy has NOT changed and is "
                f"still '{EDIT_VALUE} {RETENTION_MEASURES[EDIT_MEASURE]}' — "
                "Cancel did not overwrite the saved policy (HARD assertion)"
            ):
                expect(
                    artifacts_page.bucket_retention_measure_combobox
                ).to_have_text(
                    RETENTION_MEASURES[EDIT_MEASURE], timeout=UI_ELEMENT_TIMEOUT
                )
                expect(artifacts_page.bucket_retention_value_input).to_have_value(
                    EDIT_VALUE, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across the "
                "whole create + edit + cancel flow"
            ):
                assert not console_errors, (
                    "Unexpected console errors during the bucket retention "
                    f"edit/persistence flow: {[m.text for m in console_errors]}"
                )
        finally:
            # Teardown — the bucket is this test's own mutation and the case
            # never deletes it, so it must not leak (an earlier run's leaked
            # 'autotest-1810-b2-2251' bucket was found during analysis). The UI
            # delete path was confirmed working live; ArtifactAPI.delete_bucket()
            # is the fallback and is known to 404 in this environment (#636).
            if bucket_created:
                try:
                    self._delete_bucket_via_ui(artifacts_page, bucket_name)
                    logger.info("Teardown: deleted bucket '%s' via the UI", bucket_name)
                except Exception as ui_exc:  # noqa: BLE001 - teardown must not mask
                    logger.warning(
                        "Teardown: UI delete of '%s' failed (%s) — falling back "
                        "to the API client", bucket_name, ui_exc,
                    )
                    try:
                        artifact_api.delete_bucket(bucket_name)
                    except Exception as api_exc:  # noqa: BLE001
                        logger.warning(
                            "Teardown: API delete of '%s' also failed (known "
                            "defect #636 — delete_bucket() 404s in dev "
                            "regardless): %s", bucket_name, api_exc,
                        )
