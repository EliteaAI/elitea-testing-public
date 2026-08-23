"""UI Test for ELITEA-1818 — Create an Artifact Bucket with a 56-Character
Name, Verify the Character Indicator, and CANCEL the Delete Confirmation.

SANCTIONED RED (`.agents/testing.md` § Merge gate). This spec carries ONE
soft-asserted failure driven by one known, already-filed, deterministic
product defect — EliteaAI/elitea-testing-public#1080 — and therefore reports
pytest FAILED until the product fix ships. It is not masked and must not be
weakened: the assertion states the CORRECT expected behaviour and flips green
by itself the day #1080 is fixed.

    #1080 — Save silently does nothing on a SINGLE click at exactly 56
    characters. Root cause (analysis, 2026-08-23): the character counter is
    focus-gated and occupies 16px of flow; `mousedown` blurs the Name field →
    the counter unmounts → the Save button shifts up 16px → `mouseup` lands
    off-target → the browser emits no `click`, so `onSave` never runs. No
    request fires and the form stays open. Reproduced 4/4 at 56 characters,
    0/4 at ≤55. Real users hit this identically.

Distinct from ELITEA-1817 (`test_artifacts_create_bucket_55char_name_and_
delete.py`), the closest relative, which also creates a bucket at the 56-char
boundary: that spec asserts NO character indicator (only `aria-invalid`), and
its terminal action is the OPPOSITE one — it clicks **Delete** in the
confirmation modal and asserts the bucket is gone. This case clicks
**Cancel** and asserts the bucket REMAINS, an observable that cannot be
appended to a spec which destroys its own subject. Bucket-level
delete-cancel is covered nowhere else (ELITEA-1845 cancels a *file* delete).

Test flow (15 case steps, 1:1 with the AFS's Test Steps):
1-3. Navigate, open the New Bucket form, verify it and its defaults.
4.    Enter a unique 56-character name (kept focused — step 5 depends on it).
5.    Verify the character counter reads "0 characters left" AND that 56 is
      VALID (no aria-invalid, no helper text) — the counter is neutral
      information, not an error.
6.    Leave Retention at its Years/1 default.
7a.   SOFT — a single click on Save while the Name field is focused MUST
      submit the form. Known defect #1080.
7b.   Declared transit past #1080: blur the field, click Save, assert the
      creation POST returns 200.
8-10. Bucket listed; its dot-menu opens; the menu shows its four LIVE items.
11-12. Delete opens the shared confirmation modal; title, message and BOTH
      buttons are verified.
13-15. Cancel closes the modal WITHOUT any request, and the bucket survives.

Case-text divergence asserted as the LIVE contract (reverse-masking guard):
- Indicator text: the case says "0 of 56 remaining"; ``CharacterCounter.jsx``
  renders ```${remaining} characters left```. CLARIFICATION #1682, which also
  records the counter's focus-gating.
- Test data: the case's own "56-character" literal is 57 characters, and its
  silently-truncated form is byte-identical to ELITEA-1817's bucket name.
  A unique 56-character name is generated instead. CLARIFICATION #1683.
- Menu labels/order: the case says "Upload files, Pin to top, Edit, Delete";
  live is "Upload files / Rename / Pin to top / Delete". Pre-existing
  CLARIFICATION #666 (new occurrence commented there, not re-filed).

Fidelity: no substitution of any kind. Every asserted value is produced by
the live system — the bucket is created through the real form against the
real creation POST, the menu text is read from the live DOM, and Cancel is a
real click. The ONE declared workaround is a blur (``press("Tab")``) before
the second Save click: an ordinary user gesture used purely as TRANSIT past
#1080 to reach steps 8-15, applied only AFTER the soft assertion has recorded
the defect. Nothing is fabricated, injected, or short-circuited.
``capture_requests_matching`` is a passive listener, not a route
interception.

This case creates a bucket that its own steps deliberately do NOT delete
(step 13 cancels the deletion), so the spec owns its teardown: a try/finally
UI deletion. ``ArtifactAPI.delete_bucket()`` is not used as a fallback — it
404s in dev regardless (#636).

AFS: test-specs/artifacts/l3_create-bucket-56-char-name-limit-warning-and-delete-cancel_ELITEA-1818.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches the case priority / AFS Automation Hints)

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_create_bucket_56char_limit_warning_delete_cancel.py -v
"""

import logging
import uuid

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000        # fields, buttons, menus, modal
NAVIGATION_TIMEOUT = 15_000        # SPA route transitions
CREATE_RESPONSE_TIMEOUT = 25_000   # bucket-creation POST + response
BUCKET_LIST_TIMEOUT = 25_000       # bucket-list refetch after creation
# Bounded window in which the CORRECT behaviour (a creation POST on the first
# Save click) would land. Known defect #1080 means it currently never does, so
# this timeout is also the cost of the soft assertion — kept small on purpose.
SINGLE_CLICK_SAVE_TIMEOUT = 5_000
# The first /artifacts navigation of a fresh session renders ~970 bucket rows
# (#636) and has exceeded wait_for_page_load()'s 15s default — a condition
# wait with a bigger budget, never a sleep.
COLD_PAGE_LOAD_TIMEOUT = 60_000

MAX_BUCKET_NAME_LENGTH = 56

CREATE_FORM_HEADING = "New Bucket"
DEFAULT_BUCKET_NAME = "new-bucket"

# LIVE counter text at the limit — NOT the case's "0 of 56 remaining"
# (CLARIFICATION #1682, reverse-masking guard).
EXPECTED_COUNTER_TEXT = "0 characters left"

# LIVE bucket dot-menu text — NOT the case's "Upload files, Pin to top, Edit,
# Delete" (CLARIFICATION #666; same live string ELITEA-1817 already asserts).
EXPECTED_MENU_ITEMS_TEXT = "Upload filesRenamePin to topDelete"

EXPECTED_DELETE_DIALOG_TITLE = "Delete confirmation"
EXPECTED_CANCEL_BUTTON_TEXT = "Cancel"


def _generate_56_char_bucket_name() -> str:
    """Return a fresh, valid, EXACTLY 56-character bucket name.

    The case's own literal cannot be used: it is 57 characters
    (CLARIFICATION #1683), so ``maxLength`` silently truncates it to a value
    byte-identical to ELITEA-1817's bucket name — two specs would then create
    the same bucket. This case's bucket is also NOT deleted by its own steps
    (step 13 cancels the deletion), so a fixed name would fail the second run
    on duplicate-name (cf. ELITEA-1809), aggravated by the known cleanup leak
    #636. Satisfies the form's yup regex ``^[a-zA-Z][a-zA-Z0-9-]*$``.
    """
    filler = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6"
    return f"afs1818{uuid.uuid4().hex[:6]}{filler}"[:MAX_BUCKET_NAME_LENGTH]


@allure.epic("Artifacts")
@allure.feature("Bucket Creation + Delete Flow")
class TestArtifactCreateBucket56CharLimitWarningAndDeleteCancel:
    """ELITEA-1818 — a 56-character bucket name shows the character indicator
    and is still valid; the bucket is created; and Cancel on the bucket's
    delete confirmation closes the modal without deleting anything.

    SANCTIONED RED until #1080 ships — see the module docstring.
    """

    @pytest.mark.p2
    @allure.title(
        "A 56-character bucket name shows '0 characters left', is created, "
        "and Cancel on the delete confirmation keeps the bucket"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1818_create-bucket-56-char-name-limit-warning-cancel-delete.md",
        "onetest-ai Test Case link",
    )
    def test_create_bucket_56char_name_limit_warning_and_delete_cancel(self, page):
        """Drive the case's 15 steps end-to-end against the live system.

        Declared substitution: NONE. Declared transit (see module docstring):
        after the soft assertion for #1080 has recorded that a single Save
        click does not submit, the Name field is blurred with ``press("Tab")``
        and Save is clicked again — an ordinary user gesture, used only to
        REACH steps 8-15. Every observable this case asserts is still produced
        by the product.

        The soft failure is collected in ``soft_failures`` and raised with a
        trailing ``pytest.fail()`` (the project's established idiom for an
        observable that is not a locator — Playwright's ``expect.soft`` only
        accepts locators/pages/responses, and the observable here is the
        ABSENCE of a network request).
        """
        bucket_name = _generate_56_char_bucket_name()
        assert len(bucket_name) == MAX_BUCKET_NAME_LENGTH, (
            "Test-data sanity check: this case is meaningless at any length "
            f"other than {MAX_BUCKET_NAME_LENGTH}, got {len(bucket_name)}"
        )

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )

        artifacts_page = ArtifactsPage(page)
        soft_failures: list[str] = []
        bucket_requests = None
        bucket_created = False

        try:
            with allure.step(
                "Step 1 — Navigate to the Artifacts section — the bucket list "
                "renders"
            ):
                artifacts_page.navigate("/artifacts")
                artifacts_page.wait_for_page_load(timeout=COLD_PAGE_LOAD_TIMEOUT)
                expect(artifacts_page.buckets_heading).to_be_visible(
                    timeout=NAVIGATION_TIMEOUT
                )

            with allure.step(
                "Step 2 — Click the create-bucket folder icon above the bucket "
                "list — the 'New Bucket' form opens as a full page, not a modal"
            ):
                artifacts_page.click_create_bucket_button(timeout=NAVIGATION_TIMEOUT)
                assert "/artifacts/create-bucket" in page.url, (
                    f"Expected URL to contain '/artifacts/create-bucket', "
                    f"got: {page.url!r}"
                )

            with allure.step(
                "Step 3 — Verify the 'New Bucket' form is visible with its "
                "fields at their defaults — those defaults are what make "
                "step 6's 'left at default' assertion meaningful"
            ):
                assert (
                    artifacts_page.get_bucket_form_heading_text(
                        timeout=UI_ELEMENT_TIMEOUT
                    )
                    == CREATE_FORM_HEADING
                ), (
                    f"The form should be headed {CREATE_FORM_HEADING!r} — the "
                    "route is shared with the Edit form, so the URL alone "
                    "cannot prove the case's \"'New Bucket' form opens\""
                )
                expect(artifacts_page.bucket_name_input).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                assert (
                    artifacts_page.bucket_name_input.input_value()
                    == DEFAULT_BUCKET_NAME
                ), (
                    f"A fresh create form should pre-fill the Name field with "
                    f"{DEFAULT_BUCKET_NAME!r}, got "
                    f"{artifacts_page.bucket_name_input.input_value()!r}"
                )
                assert artifacts_page.get_retention_measure_text() == "Years", (
                    "Retention measure should default to 'Years'"
                )
                assert artifacts_page.get_retention_value() == "1", (
                    "Retention value should default to '1'"
                )
                expect(artifacts_page.bucket_save_button).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                f"Step 4 — Enter the {MAX_BUCKET_NAME_LENGTH}-character bucket "
                "name — the field accepts it in full. Focus is deliberately "
                "LEFT in the field: the character counter is focus-gated and "
                "unmounts on blur (CLARIFICATION #1682)"
            ):
                artifacts_page.fill_bucket_name(bucket_name)
                filled_value = artifacts_page.bucket_name_input.input_value()
                assert filled_value == bucket_name, (
                    f"Name field should hold {bucket_name!r} after filling, "
                    f"got {filled_value!r}"
                )
                assert len(filled_value) == MAX_BUCKET_NAME_LENGTH, (
                    f"Name field should hold all {MAX_BUCKET_NAME_LENGTH} "
                    f"characters, got length {len(filled_value)}"
                )

            with allure.step(
                "Step 5 — Verify the character-limit indicator reads "
                f"{EXPECTED_COUNTER_TEXT!r} — the LIVE text, not the case's "
                "'0 of 56 remaining' (CLARIFICATION #1682) — AND that 56 is "
                "still VALID: the indicator is neutral information, not an "
                "error state, which is what makes the case's 'warning' "
                "framing a real assertion rather than a guess"
            ):
                expect(artifacts_page.bucket_name_character_counter).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                counter_text = artifacts_page.get_bucket_name_character_counter_text(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                assert counter_text == EXPECTED_COUNTER_TEXT, (
                    f"Expected the character counter to read "
                    f"{EXPECTED_COUNTER_TEXT!r} at the limit, got "
                    f"{counter_text!r}"
                )
                assert not artifacts_page.is_bucket_name_invalid(
                    timeout=UI_ELEMENT_TIMEOUT
                ), (
                    "A 56-character name is VALID — the Name field must not be "
                    "flagged aria-invalid at the boundary"
                )
                expect(artifacts_page.bucket_name_helper_text).to_have_count(
                    0, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 6 — Leave the Retention policy at its default — it is "
                "still Years/1 after the name was typed"
            ):
                assert artifacts_page.get_retention_measure_text() == "Years", (
                    "Retention measure should remain 'Years'"
                )
                assert artifacts_page.get_retention_value() == "1", (
                    "Retention value should remain '1'"
                )

            with allure.step(
                "Step 7a — SANCTIONED RED (Known defect: #1080) — a SINGLE "
                "click on Save while the Name field is focused MUST submit "
                "the form and fire the bucket-creation POST. Live it does "
                "not: mousedown blurs the field, the focus-gated counter "
                "unmounts, the Save button shifts up 16px, mouseup lands "
                "off-target and no click event is emitted. Asserted as the "
                "CORRECT behaviour and collected as a soft failure — never "
                "weakened, skipped or inverted"
            ):
                create_response = None
                # Known defect: #1080 — soft-assert the CORRECT behaviour.
                try:
                    with page.expect_response(
                        lambda r: "artifacts/buckets" in r.url
                        and r.request.method == "POST",
                        timeout=SINGLE_CLICK_SAVE_TIMEOUT,
                    ) as response_info:
                        artifacts_page.bucket_save_button.click()
                    create_response = response_info.value
                except PlaywrightTimeoutError:
                    soft_failures.append(
                        "Known defect: #1080 — a single click on Save with a "
                        f"{MAX_BUCKET_NAME_LENGTH}-character name in the "
                        "focused Name field fired NO bucket-creation POST "
                        f"within {SINGLE_CLICK_SAVE_TIMEOUT}ms; the form "
                        "stayed open. Expected: the bucket is saved on the "
                        "first click (case step 7)."
                    )
                    logger.warning(
                        "Known defect #1080 reproduced: no creation POST on "
                        "the first Save click"
                    )

            with allure.step(
                "Step 7b — DECLARED TRANSIT past #1080 (not a substitution): "
                "blur the Name field with a real Tab keystroke — exactly what "
                "a user does when the first click appears to do nothing — and "
                "click Save again. Verify the bucket-creation POST returns "
                "200. Skipped entirely once #1080 is fixed and step 7a's "
                "single click already created the bucket"
            ):
                if create_response is None:
                    artifacts_page.bucket_name_input.press("Tab")
                    create_response = artifacts_page.click_bucket_save_button(
                        timeout=CREATE_RESPONSE_TIMEOUT
                    )
                bucket_created = True
                assert create_response.status == 200, (
                    f"Bucket creation POST should return 200, got "
                    f"{create_response.status} for {create_response.url}"
                )

            with allure.step(
                "Step 8 — Verify the bucket appears in the left-panel bucket "
                "list — a condition wait on the bucket's own dynamic testid, "
                "never a count read straight after Save (the list refetches "
                "asynchronously)"
            ):
                artifacts_page.wait_for_bucket_in_list(
                    bucket_name, timeout=BUCKET_LIST_TIMEOUT
                )

            with allure.step(
                "Step 9 — Hover the bucket row and click its 3-dot actions "
                "menu trigger — the dropdown opens"
            ):
                artifacts_page.open_bucket_menu(bucket_name, timeout=UI_ELEMENT_TIMEOUT)
                expect(
                    artifacts_page.bucket_menu_upload_files_menuitem
                ).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 10 — Verify the dropdown shows all four options — LIVE "
                "label and order (CLARIFICATION #666: the live label is "
                "'Rename', not the case's 'Edit', and the live order puts "
                "'Pin to top' third; reverse-masking guard — assert the "
                "product's contract, not the case's stale wording)"
            ):
                menu_text = artifacts_page.get_bucket_menu_items_text(
                    bucket_name, timeout=UI_ELEMENT_TIMEOUT
                )
                assert menu_text == EXPECTED_MENU_ITEMS_TEXT, (
                    f"Expected the bucket-menu dropdown's live text to be "
                    f"{EXPECTED_MENU_ITEMS_TEXT!r}, got {menu_text!r}"
                )

            with allure.step(
                "Step 11 — Click 'Delete' in the open dropdown — the "
                "delete-confirmation modal opens"
            ):
                artifacts_page.click_bucket_menu_delete_item(timeout=UI_ELEMENT_TIMEOUT)
                expect(artifacts_page.delete_confirm_dialog).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 12 — Verify the 'Delete confirmation' modal: its title, "
                "its message naming this bucket, and BOTH buttons. The "
                "message's live wording is already tracked as CLARIFICATION "
                "#664; this case's own text asks only for 'the correct "
                "message', so no new clarification is owed"
            ):
                dialog_title = (
                    artifacts_page.delete_confirm_title.text_content() or ""
                ).strip()
                assert dialog_title == EXPECTED_DELETE_DIALOG_TITLE, (
                    f"Expected the modal title {EXPECTED_DELETE_DIALOG_TITLE!r}, "
                    f"got {dialog_title!r}"
                )
                message_text = artifacts_page.get_delete_confirm_message_text(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                expected_message = (
                    f"Are you sure to delete the {bucket_name}? "
                    "It can't be restored."
                )
                assert message_text == expected_message, (
                    f"Expected live confirm message {expected_message!r}, got "
                    f"{message_text!r}"
                )
                expect(artifacts_page.delete_confirm_button).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                expect(artifacts_page.delete_confirm_cancel_button).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                cancel_text = (
                    artifacts_page.delete_confirm_cancel_button.text_content() or ""
                ).strip()
                assert cancel_text == EXPECTED_CANCEL_BUTTON_TEXT, (
                    f"Expected the modal's dismiss button to read "
                    f"{EXPECTED_CANCEL_BUTTON_TEXT!r}, got {cancel_text!r}"
                )

            with allure.step(
                "Step 13 — Arm a passive capture on any artifacts/buckets "
                "request, then click 'Cancel' in the modal. The network is "
                "the only oracle that can tell 'not deleted' apart from "
                "'deletion attempted and failed' — a DOM-only check would "
                "pass even if a DELETE had fired"
            ):
                bucket_requests = artifacts_page.capture_requests_matching(
                    "artifacts/buckets"
                )
                artifacts_page.click_delete_cancel_button(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 14 — Verify the delete-confirmation modal is closed"
            ):
                expect(artifacts_page.delete_confirm_dialog).not_to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 15 — Verify the bucket is STILL listed and was not "
                "deleted: its row is visible, exactly one row carries its "
                "name, and no artifacts/buckets request fired across the "
                "whole cancel window (steps 13-15)"
            ):
                expect(artifacts_page.bucket_row(bucket_name)).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                assert artifacts_page.count_bucket_rows(bucket_name) == 1, (
                    f"'{bucket_name}' should still be listed exactly once "
                    "after cancelling its deletion, got "
                    f"{artifacts_page.count_bucket_rows(bucket_name)}"
                )
                assert list(bucket_requests) == [], (
                    "Cancel must fire NO artifacts/buckets request at all — "
                    f"captured: {list(bucket_requests)!r}"
                )

            with allure.step(
                "Side-channel check — no unexpected console errors across the "
                "whole create + delete-cancel flow"
            ):
                assert not console_errors, (
                    "Unexpected console errors during the 56-char bucket "
                    f"create + delete-cancel flow: "
                    f"{[m.text for m in console_errors]}"
                )

            if soft_failures:
                # SANCTIONED RED — the flow above passed cleanly; the only
                # failure is the known, filed, deterministic product defect.
                pytest.fail(
                    "Known product defect(s) reproduced (everything else in "
                    "this case passed cleanly):\n" + "\n".join(soft_failures)
                )
        finally:
            if bucket_requests is not None:
                # A leaked listener can hang later tests.
                bucket_requests.stop()
            if bucket_created:
                # This case's own steps deliberately KEEP the bucket (step 13
                # cancels its deletion), so the spec owns the teardown. Never
                # fail the test on cleanup. ArtifactAPI.delete_bucket() is not
                # used as a fallback — it 404s in dev regardless (#636).
                try:
                    artifacts_page.delete_bucket_via_menu(
                        bucket_name, timeout=BUCKET_LIST_TIMEOUT
                    )
                    logger.info("Teardown: deleted bucket '%s' via the UI", bucket_name)
                except Exception as exc:
                    logger.warning(
                        "Teardown could not delete bucket '%s' via the UI: %s",
                        bucket_name, exc,
                    )
