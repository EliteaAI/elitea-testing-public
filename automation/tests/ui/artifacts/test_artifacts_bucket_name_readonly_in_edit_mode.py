"""UI Test for ELITEA-1816 — A Mixed-Case Bucket Name Is Stored in Lowercase,
and the Name Field Is Read-Only in Edit Mode While Retention Stays Editable.

Regression test for the bucket EDIT form's field-level contract, which no
existing spec touches: the nearest neighbour, ELITEA-1810
(``test_artifacts_bucket_retention_edit_persistence.py``), opens the same edit
form but creates its bucket with an already-lowercase name and never reads the
Name field's editability — ``grep -rn "is_disabled|is_editable"
tests/ui/artifacts/`` had no hit on this field anywhere in the suite.

Test flow (17 case steps, 1:1 with the AFS's Test Steps):
1-2.   Navigate to Artifacts, click the create-bucket folder icon (full page
       nav to ``/artifacts/create-bucket``, not a modal) — headed ``New
       Bucket``. The heading is asserted, not just the URL: Step 11 below
       asserts ``Edit bucket`` on that SAME URL, so the route cannot tell the
       two forms apart.
3.     Type a MIXED-CASE bucket name — preserved verbatim, and the field is
       ENABLED here. That enabled reading is the control for Step 15: without
       it, "disabled in Edit mode" would also pass on a field that is always
       disabled.
4-5.   Set the retention policy to ``Days`` / ``1`` (the case's own data).
6.     Save — the creation POST returns 200 AND its response body's ``name``
       is the all-lowercase form (the storage layer's own statement; the DOM
       cannot distinguish stored-lowercase from rendered-lowercase).
7.     The bucket is listed in lowercase — lowercase-keyed row present,
       mixed-case-keyed row absent (count 0), row text all-lowercase.
8-9.   Hover the row, open its dot-menu, verify its four items.
10-11. Click the edit entry — the form reopens headed "Edit bucket" (the SAME
       route serves create and edit, so the heading text, not the URL, is what
       tells them apart).
12-13. The Name field shows the lowercase name; retention reads back
       ``Days`` / ``1`` (HARD assertions — unaffected by #1677, which only
       mangles a Months policy).
14-15. Click into the Name field and try to type/delete: the click is REFUSED
       (Playwright's actionability check on a disabled element), the field is
       neither editable nor enabled, and — the assertion that actually proves
       "no input is accepted" — its value is UNCHANGED after the keystrokes.
16.    Retention stays editable in the same form: the measure is actually
       CHANGED to Weeks and the value to 3 (an actual edit, not an attribute
       read — "editable" is only proven by a value that really changed).
17.    Cancel — no bucket PUT fires (asserted via a listener armed BEFORE the
       click, so a Cancel regression localises to this step), the list
       returns, and reopening the form still shows ``Days`` / ``1``: the
       discarded ``Weeks / 3`` never reached storage.

Case-text divergences asserted as the LIVE contract (reverse-masking guard):
- Steps 9/10 call the edit entry "Edit" and list the items in a different
  order; the live dot-menu reads ``Upload files`` / ``Rename`` / ``Pin to
  top`` / ``Delete``. Tracked CLARIFICATION #666 (this occurrence was
  commented onto it during analysis, not re-filed). Asserting the stale case
  text would be reverse-masking.
- Steps 14/15 say "read-only"; the product implements non-editability as a
  real ``disabled`` attribute (``CreateBucket.jsx`` renders the field with
  ``disabled={!!currentBucket}``) — ``readonly`` is absent from the DOM. The
  case's observable ("no text cursor appears; no input is accepted") holds
  exactly, so this is terminology, not drift — hence both ``is_editable() is
  False`` and ``is_disabled() is True`` are asserted, and no ``readonly``
  attribute is hunted.
- The case's literal ``BuCkEt-Mix`` is a placeholder — a unique mixed-case
  name is generated per run and the expectation DERIVED from it
  (``typed.lower()``), never hardcoded.

Retention probe note: Step 16 uses ``Weeks`` deliberately, never ``Months`` —
open defect #1677 makes a Months policy reopen as Days, which would inject an
unrelated red into this case.

Fidelity: no substitution of any kind. The bucket is created through the real
UI (the ``artifact_bucket`` API fixture is deliberately NOT used — creating it
with a mixed-case name IS case steps 2-6, and the stored name is the subject
of steps 7 and 12), and both storage assertions read real network traffic.

AFS: test-specs/artifacts/l3_bucket-name-readonly-in-edit-mode-and-lowercase_ELITEA-1816.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p3: low priority (matches case priority "medium" / AFS l3)

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_bucket_name_readonly_in_edit_mode.py -v
"""

import logging
import time

import allure
import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect

from pages.artifacts_page import ArtifactsPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000        # fields, buttons, menus, rows
NAVIGATION_TIMEOUT = 15_000        # SPA route transitions
SAVE_RESPONSE_TIMEOUT = 20_000     # bucket-creation POST
# The project under test carries ~970 buckets (#636) and the left panel
# refetches the WHOLE list after a save — condition wait on the row's own
# testid, never a sleep, but with a larger budget than the SPA transitions.
BUCKET_LIST_TIMEOUT = 45_000
# Step 14 asserts a click is REFUSED. That refusal is observed as a timeout, so
# the budget is deliberately SHORT: the assertion is "the click never becomes
# actionable", and a long timeout would only make the test look hung.
REFUSED_INTERACTION_TIMEOUT = 3_000

# ---------------------------------------------------------------------------
# Test data (from the case's own Test Data table, used verbatim live)
# ---------------------------------------------------------------------------
# Retention policy the bucket is CREATED with (case steps 4-5) and must read
# back with (step 13) and still carry after the discarded edit (step 17).
CREATE_MEASURE = "days"
CREATE_MEASURE_LABEL = "Days"
CREATE_VALUE = "1"

# Step 16's editability probe — any change proves editability, and it is
# discarded by Step 17's Cancel. Deliberately NOT "months" (#1677).
PROBE_MEASURE = "weeks"
PROBE_MEASURE_LABEL = "Weeks"
PROBE_VALUE = "3"

# ``/artifacts/create-bucket`` is a SINGLE route serving both flows —
# ``CreateBucket.jsx:214`` renders ``currentBucket ? 'Edit bucket' : 'New
# Bucket'`` — so the heading text, not the URL, is what tells the two forms
# apart (Step 2 asserts the create heading, Step 11 the edit heading).
CREATE_FORM_HEADING = "New Bucket"
EDIT_FORM_HEADING = "Edit bucket"

# The four dot-menu items, in their live render order (CLARIFICATION #666 —
# the case text says "Edit" and lists a different order). The menu container's
# text is the concatenation of its sibling Typographies, with no separators.
BUCKET_MENU_ITEM_LABELS = ["Upload files", "Rename", "Pin to top", "Delete"]
BUCKET_MENU_ITEMS_TEXT = "".join(BUCKET_MENU_ITEM_LABELS)

# The bucket-update request an edit save fires. Cancel must fire NONE of these
# — case Step 17's "closes without saving".
BUCKET_REQUEST_SUBSTRING = "artifacts/buckets"


@allure.epic("Artifacts")
@allure.feature("Bucket Edit Form")
class TestArtifactBucketNameReadOnlyInEditMode:
    """ELITEA-1816 — a mixed-case name stores lowercase; the Edit form's Name
    field is non-editable while its retention controls stay editable."""

    @pytest.mark.p3
    @allure.title(
        "A mixed-case bucket name is stored lowercase, and in Edit mode the "
        "Name field is read-only while the retention policy stays editable"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1816_bucket-name-readonly-in-edit-mode-lowercase.md",
        "onetest-ai Test Case link",
    )
    def test_bucket_name_readonly_in_edit_mode_and_stored_lowercase(
        self, page, artifact_api
    ):
        """Drive the case's 17 steps end-to-end against the live system."""
        typed_name = f"AuToTest-1816-{int(time.time())}"
        expected_name = typed_name.lower()

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
                "navigation, not a modal. The route is shared with the edit "
                "form (Step 11), so the heading text is what proves this is "
                "the CREATE form"
            ):
                artifacts_page.click_create_bucket_button(timeout=NAVIGATION_TIMEOUT)
                assert "/artifacts/create-bucket" in page.url, (
                    f"Expected URL to contain '/artifacts/create-bucket', "
                    f"got: {page.url!r}"
                )
                assert (
                    artifacts_page.get_bucket_form_heading_text(
                        timeout=UI_ELEMENT_TIMEOUT
                    )
                    == CREATE_FORM_HEADING
                ), (
                    f"The form should be headed {CREATE_FORM_HEADING!r} — this "
                    f"spec's own Step 11 asserts {EDIT_FORM_HEADING!r} on the "
                    "SAME URL, so the URL cannot prove the case's "
                    "\"'New Bucket' form opens\" on its own"
                )

            with allure.step(
                f"Step 3 — Enter the bucket name in MIXED CASE ({typed_name!r}; "
                "the case's literal 'BuCkEt-Mix' is a placeholder) — verify the "
                "field preserves it verbatim AND is ENABLED here (the control "
                "for Step 15)"
            ):
                artifacts_page.fill_bucket_name(typed_name)
                assert artifacts_page.bucket_name_input.input_value() == typed_name, (
                    "The Name field should preserve the typed mixed-case name "
                    f"{typed_name!r} verbatim (the conversion is server-side), "
                    f"got {artifacts_page.bucket_name_input.input_value()!r}"
                )
                assert (
                    artifacts_page.is_bucket_name_input_disabled(
                        timeout=UI_ELEMENT_TIMEOUT
                    )
                    is False
                ), (
                    "The Name field must be ENABLED on the create form — "
                    "without this control, Step 15's 'disabled in Edit mode' "
                    "would also pass on a field that is always disabled"
                )
                assert (
                    artifacts_page.is_bucket_name_input_editable(
                        timeout=UI_ELEMENT_TIMEOUT
                    )
                    is True
                ), "The Name field must be editable on the create form"

            with allure.step(
                f"Step 4 — Open the Retention policy dropdown and select "
                f"{CREATE_MEASURE_LABEL!r}"
            ):
                artifacts_page.open_retention_measure_dropdown(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                artifacts_page.select_retention_measure(
                    CREATE_MEASURE, timeout=UI_ELEMENT_TIMEOUT
                )
                assert (
                    artifacts_page.get_retention_measure_text()
                    == CREATE_MEASURE_LABEL
                ), (
                    f"Retention measure should read {CREATE_MEASURE_LABEL!r}, "
                    f"got {artifacts_page.get_retention_measure_text()!r}"
                )

            with allure.step(
                f"Step 5 — Enter the retention value {CREATE_VALUE!r} in the "
                "numerical field"
            ):
                artifacts_page.set_retention_value(CREATE_VALUE)
                assert artifacts_page.get_retention_value() == CREATE_VALUE, (
                    f"Retention value field should show {CREATE_VALUE!r}, got "
                    f"{artifacts_page.get_retention_value()!r}"
                )

            with allure.step(
                "Step 6 — Click Save — verify the bucket-creation POST returns "
                "200 AND its response body names the bucket in LOWERCASE (the "
                "'stored' half of the case)"
            ):
                create_response = artifacts_page.click_bucket_save_button(
                    timeout=SAVE_RESPONSE_TIMEOUT
                )
                bucket_created = True
                assert create_response.status == 200, (
                    f"Bucket creation POST should return 200, got "
                    f"{create_response.status} for {create_response.url}"
                )
                stored_name = create_response.json()["name"]
                assert stored_name == expected_name, (
                    f"The backend should store the typed {typed_name!r} as "
                    f"{expected_name!r}; the creation response says "
                    f"{stored_name!r}"
                )

            with allure.step(
                f"Step 7 — Verify the bucket is listed as {expected_name!r} "
                "(all lowercase): lowercase-keyed row present, mixed-case-keyed "
                "row absent, row text carrying no uppercase character"
            ):
                artifacts_page.wait_for_bucket_in_list(
                    expected_name, timeout=BUCKET_LIST_TIMEOUT
                )
                assert artifacts_page.count_bucket_rows(expected_name) == 1, (
                    f"Expected exactly one {expected_name!r} row in the bucket "
                    "list (the row testid is derived from the STORED name)"
                )
                assert artifacts_page.count_bucket_rows(typed_name) == 0, (
                    f"No row keyed by the typed mixed-case name {typed_name!r} "
                    "should exist — without this negative half, a UI rendering "
                    "BOTH forms would pass"
                )
                row_text = (
                    artifacts_page.bucket_row(expected_name).text_content() or ""
                ).strip()
                assert row_text == expected_name, (
                    f"The bucket row should read exactly {expected_name!r}, got "
                    f"{row_text!r}"
                )
                assert row_text == row_text.lower(), (
                    "The displayed bucket name must contain no uppercase "
                    f"character, got {row_text!r}"
                )

            with allure.step(
                "Step 8 — Hover the bucket row and click its 3-dot ellipsis "
                "icon — verify the dropdown appears (the trigger is hidden "
                "until the row is hovered)"
            ):
                artifacts_page.open_bucket_menu(
                    expected_name, timeout=UI_ELEMENT_TIMEOUT
                )
                expect(
                    artifacts_page.bucket_menu_container(expected_name)
                ).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 9 — Verify the dropdown offers all four options — LIVE "
                "labels/order are 'Upload files' / 'Rename' / 'Pin to top' / "
                "'Delete'; the case text says 'Edit' and lists another order "
                "(CLARIFICATION #666, reverse-masking guard: assert the "
                "product's live contract)"
            ):
                menu_text = artifacts_page.get_bucket_menu_items_text(
                    expected_name, timeout=UI_ELEMENT_TIMEOUT
                )
                assert menu_text == BUCKET_MENU_ITEMS_TEXT, (
                    f"Bucket dot-menu should offer exactly "
                    f"{BUCKET_MENU_ITEM_LABELS} in that order (concatenated "
                    f"{BUCKET_MENU_ITEMS_TEXT!r}), got {menu_text!r}"
                )

            with allure.step(
                "Step 10 — Click the edit entry ('Rename' live, 'Edit' in the "
                "case text — CLARIFICATION #666)"
            ):
                artifacts_page.click_bucket_menu_rename_item(
                    timeout=NAVIGATION_TIMEOUT
                )

            with allure.step(
                "Step 11 — Verify the 'Edit bucket' form is open — the SAME "
                "route serves create and edit, so the heading text (not the "
                "URL) is what tells them apart"
            ):
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
                    f"The form should be headed {EDIT_FORM_HEADING!r} when "
                    "reached via the dot-menu's edit entry"
                )

            with allure.step(
                f"Step 12 — Verify the Name field displays the LOWERCASE name "
                f"{expected_name!r}"
            ):
                expect(artifacts_page.bucket_name_input).to_have_value(
                    expected_name, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                f"Step 13 — Verify the retention policy reads back as "
                f"{CREATE_MEASURE_LABEL!r} / {CREATE_VALUE!r} (HARD "
                "assertions — #1677 only mangles a Months policy)"
            ):
                assert (
                    artifacts_page.get_retention_measure_text()
                    == CREATE_MEASURE_LABEL
                ), (
                    f"Retention measure should read back {CREATE_MEASURE_LABEL!r}, "
                    f"got {artifacts_page.get_retention_measure_text()!r}"
                )
                assert artifacts_page.get_retention_value() == CREATE_VALUE, (
                    f"Retention value should read back {CREATE_VALUE!r}, got "
                    f"{artifacts_page.get_retention_value()!r}"
                )

            with allure.step(
                "Step 14 — Attempt to click into the Name field and modify it — "
                "the click is REFUSED (Playwright's actionability check refuses "
                "a disabled element), then keystrokes are sent anyway so Step "
                "15 can prove none of them was accepted"
            ):
                with pytest.raises(PlaywrightTimeoutError):
                    artifacts_page.bucket_name_input.click(
                        timeout=REFUSED_INTERACTION_TIMEOUT
                    )
                # The keystroke attempt is the honest half of "try to type or
                # delete characters". Playwright's deprecated Locator.type()
                # was confirmed live NOT to raise on this disabled input (it
                # silently does nothing), but press() may — either outcome is
                # acceptable here, because what PROVES no input was accepted is
                # Step 15's unchanged value, not this call's outcome. Wrapped
                # with the same short budget so a refusal cannot look like a
                # hang.
                for attempt in (
                    lambda: artifacts_page.bucket_name_input.type(
                        "XYZ", timeout=REFUSED_INTERACTION_TIMEOUT
                    ),
                    lambda: artifacts_page.bucket_name_input.press(
                        "Backspace", timeout=REFUSED_INTERACTION_TIMEOUT
                    ),
                ):
                    try:
                        attempt()
                    except PlaywrightTimeoutError:
                        logger.info(
                            "Keystroke attempt refused by the disabled Name "
                            "field (expected)"
                        )

            with allure.step(
                "Step 15 — Verify the Name field is read-only and unchanged: "
                "not editable, disabled, and — the assertion that actually "
                "proves 'no input is accepted' — its value survived Step 14's "
                "keystrokes intact"
            ):
                assert (
                    artifacts_page.is_bucket_name_input_editable(
                        timeout=UI_ELEMENT_TIMEOUT
                    )
                    is False
                ), "The Name field must NOT be editable in Edit mode"
                assert (
                    artifacts_page.is_bucket_name_input_disabled(
                        timeout=UI_ELEMENT_TIMEOUT
                    )
                    is True
                ), (
                    "The Name field must be disabled in Edit mode — the product "
                    "implements 'read-only' as a real disabled attribute "
                    "(CreateBucket.jsx: disabled={!!currentBucket}); there is "
                    "no readonly attribute to assert"
                )
                assert (
                    artifacts_page.bucket_name_input.input_value() == expected_name
                ), (
                    f"The Name field's value must still be {expected_name!r} "
                    "after the typing/deleting attempt, got "
                    f"{artifacts_page.bucket_name_input.input_value()!r}"
                )

            with allure.step(
                "Step 16 — Verify the retention dropdown and numerical field "
                f"remain editable — actually change them to "
                f"{PROBE_MEASURE_LABEL!r} / {PROBE_VALUE!r} ('editable' is only "
                "proven by a value that really changed)"
            ):
                artifacts_page.select_retention_measure(
                    PROBE_MEASURE, timeout=UI_ELEMENT_TIMEOUT
                )
                assert (
                    artifacts_page.get_retention_measure_text()
                    == PROBE_MEASURE_LABEL
                ), (
                    f"Retention measure should now read {PROBE_MEASURE_LABEL!r}, "
                    f"got {artifacts_page.get_retention_measure_text()!r}"
                )
                artifacts_page.set_retention_value(PROBE_VALUE)
                assert artifacts_page.get_retention_value() == PROBE_VALUE, (
                    f"Retention value field should show {PROBE_VALUE!r}, got "
                    f"{artifacts_page.get_retention_value()!r}"
                )
                assert artifacts_page.bucket_retention_value_input.is_editable(), (
                    "The retention value field must be editable in Edit mode"
                )

            # Arm the bucket-PUT listener BEFORE the Cancel click, so "closes
            # without saving" is proven by the ABSENCE of the request itself
            # rather than inferred afterwards from the reopened form.
            cancel_puts = artifacts_page.capture_requests_matching(
                BUCKET_REQUEST_SUBSTRING, method="PUT"
            )
            try:
                with allure.step(
                    "Step 17a — Click Cancel — verify the form closes back to "
                    "the bucket list and NO bucket-update PUT fired"
                ):
                    artifacts_page.click_bucket_cancel_button(
                        timeout=NAVIGATION_TIMEOUT
                    )
                    assert list(cancel_puts) == [], (
                        "Cancel must not save: expected no bucket PUT request, "
                        f"but captured {list(cancel_puts)!r}"
                    )
                    assert (
                        "/artifacts" in page.url
                        and "/artifacts/create-bucket" not in page.url
                    ), (
                        "Cancel should leave the bucket form and land back on "
                        f"the Artifacts list, got {page.url!r}"
                    )
                    artifacts_page.wait_for_bucket_in_list(
                        expected_name, timeout=BUCKET_LIST_TIMEOUT
                    )
            finally:
                cancel_puts.stop()

            with allure.step(
                "Step 17b — Reopen the edit form and verify the retention "
                f"policy is STILL {CREATE_MEASURE_LABEL!r} / {CREATE_VALUE!r} — "
                "the durable half of 'without saving': the discarded "
                f"{PROBE_MEASURE_LABEL} / {PROBE_VALUE} never reached storage"
            ):
                artifacts_page.open_bucket_menu(
                    expected_name, timeout=UI_ELEMENT_TIMEOUT
                )
                artifacts_page.click_bucket_menu_rename_item(
                    timeout=NAVIGATION_TIMEOUT
                )
                assert (
                    artifacts_page.get_bucket_form_heading_text(
                        timeout=UI_ELEMENT_TIMEOUT
                    )
                    == EDIT_FORM_HEADING
                ), f"The form should be headed {EDIT_FORM_HEADING!r}"
                expect(
                    artifacts_page.bucket_retention_measure_combobox
                ).to_have_text(CREATE_MEASURE_LABEL, timeout=UI_ELEMENT_TIMEOUT)
                expect(artifacts_page.bucket_retention_value_input).to_have_value(
                    CREATE_VALUE, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across the "
                "whole create + edit + cancel flow"
            ):
                assert not console_errors, (
                    "Unexpected console errors during the bucket read-only-name "
                    f"flow: {[m.text for m in console_errors]}"
                )
        finally:
            # Teardown — the bucket is this test's own mutation and the case
            # never deletes it, so it must not leak into a project already
            # carrying ~970 buckets (#636). UI delete is the confirmed path;
            # ArtifactAPI.delete_bucket() 404s in this environment (#636).
            if bucket_created:
                try:
                    artifacts_page.delete_bucket_via_menu(
                        expected_name, timeout=BUCKET_LIST_TIMEOUT
                    )
                    logger.info(
                        "Teardown: deleted bucket '%s' via the UI", expected_name
                    )
                except Exception as ui_exc:  # noqa: BLE001 - teardown must not mask
                    logger.warning(
                        "Teardown: UI delete of '%s' failed (%s) — falling back "
                        "to the API client", expected_name, ui_exc,
                    )
                    try:
                        artifact_api.delete_bucket(expected_name)
                    except Exception as api_exc:  # noqa: BLE001
                        logger.warning(
                            "Teardown: API delete of '%s' also failed (known "
                            "defect #636 — delete_bucket() 404s in dev "
                            "regardless): %s", expected_name, api_exc,
                        )
