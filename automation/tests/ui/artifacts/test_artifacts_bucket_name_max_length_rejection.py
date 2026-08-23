"""UI Test for ELITEA-1819 — the Bucket Name Field Does Not Accept More Than
56 Characters.

The UPPER bound of the New Bucket form's Name field, which no merged spec
asserts: ``test_artifacts_bucket_name_validation_invalid_formats.py``
(ELITEA-1811/1814) covers the *regex* rule, ``test_artifacts_bucket_empty_
name_validation.py`` (ELITEA-1813) covers the *lower* bound (empty name), and
``test_artifacts_create_bucket_55char_name_and_delete.py`` (ELITEA-1817) fills
a 56-character name but never attempts a 57th character and never reads the
character counter.

Enforcement mechanism (live-confirmed): ``CreateBucket.jsx:239-241`` sets
``inputProps={{ maxLength: 56 }}`` — a NATIVE browser input constraint, so the
57th keystroke never reaches React. There is no error state, no helper text
and no toast: the character is simply dropped. That is what steps 7-8 pin.

Test flow (9 case steps, 1:1 with the AFS's Test Steps):
1. Navigate to Artifacts.
2. Open the New Bucket form (full page navigation, not a modal).
3. Verify the form, its pre-filled ``new-bucket`` default AND the Name
   field's own ``maxlength="56"`` attribute — the contract this case exists
   to enforce, asserted at its cause rather than only at its symptom.
4. Enter a genuine 56-character name (kept focused — step 5 depends on it).
5. Verify the character counter reads "0 characters left".
6. Attempt a 57th character as a REAL keystroke.
7. Verify it was rejected — value unchanged, still 56, no trailing "z" —
   for BOTH delivery shapes (``type()`` and ``press()``).
8. Verify the counter still reads "0 characters left" and that the rejection
   is SILENT (no aria-invalid, no helper text).
9. Verify the name is unchanged (the case brackets step 8 with two field
   assertions; both are kept).

Case-text divergence asserted as the LIVE contract (reverse-masking guard):
- The case's indicator text "0 of 56 remaining" does not exist in the
  product. ``CharacterCounter.jsx`` renders ```${remaining} characters
  left``` — the live string is "0 characters left". Filed as case-text
  CLARIFICATION #1682, which also records that the counter is FOCUS-GATED
  (``isFocused('name') && length === 56``): it is removed from the DOM
  entirely on blur, so it is never asserted after focus leaves the field.
- The case's own 56-character literal is in fact 57 characters. Typing it
  would already perform step 6's rejection and collapse steps 4 and 6 into a
  single action, destroying the case's structure. A genuine 56-character name
  is generated instead. Filed as case-data CLARIFICATION #1683.

Fidelity: no substitution of any kind. The extra character is delivered as a
real key event — ``fill()`` is deliberately NOT used anywhere near it,
because it writes through the DOM value setter and bypasses ``maxLength``
entirely, which would make this test pass for the wrong reason.
``capture_requests_matching`` is a passive listener, not a route
interception.

Read-only by construction: the case never clicks Save, so nothing is created,
nothing is persisted, and there is no teardown — the spec leaks no bucket
into a project already carrying ~970 of them (#636).

AFS: test-specs/artifacts/l3_bucket-name-field-rejects-more-than-56-characters_ELITEA-1819.md

Markers:
    - ui: requires browser
    - regression: regression test
    - p2: medium priority (matches the case priority / AFS Automation Hints)

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_bucket_name_max_length_rejection.py -v
"""

import logging
import uuid

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000        # fields, counter, helper text
NAVIGATION_TIMEOUT = 15_000        # SPA route transitions
# The first /artifacts navigation of a fresh session renders ~970 bucket rows
# (#636) and has exceeded wait_for_page_load()'s 15s default — a condition
# wait with a bigger budget, never a sleep.
COLD_PAGE_LOAD_TIMEOUT = 60_000

MAX_BUCKET_NAME_LENGTH = 56

# The single route /artifacts/create-bucket serves BOTH the create and edit
# forms; only the heading text discriminates them.
CREATE_FORM_HEADING = "New Bucket"

# The form's own pre-filled default (CreateBucket.jsx initialValues.name).
DEFAULT_BUCKET_NAME = "new-bucket"

# The extra, must-be-rejected character (the case's own choice).
EXTRA_CHARACTER = "z"

# LIVE counter text at the limit (CharacterCounter.jsx renders
# `${remaining} characters left`; the ". You have reached the MAXIMUM
# character limit" suffix is suppressed at this call site via
# `hideMaxLimitMessage`). NOT the case's "0 of 56 remaining" —
# CLARIFICATION #1682, reverse-masking guard.
EXPECTED_COUNTER_TEXT = "0 characters left"


def _generate_56_char_bucket_name() -> str:
    """Return a fresh, valid, EXACTLY 56-character bucket name.

    The case's own literal is 57 characters (CLARIFICATION #1683) and cannot
    be used: typing it would already exercise step 6's rejection inside step
    4. Satisfies the form's yup regex ``^[a-zA-Z][a-zA-Z0-9-]*$``. Nothing is
    persisted by this case, so uniqueness is not strictly required — it is
    generated anyway so a stray Save during future maintenance can never
    collide with ELITEA-1817's or ELITEA-1818's bucket names.
    """
    filler = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6"
    return f"afs1819{uuid.uuid4().hex[:6]}{filler}"[:MAX_BUCKET_NAME_LENGTH]


@allure.epic("Artifacts")
@allure.feature("Bucket Creation — Name Validation")
class TestArtifactBucketNameMaxLengthRejection:
    """ELITEA-1819 — the Name field enforces a hard 56-character maximum: a
    57th keystroke is dropped silently, the value stays byte-identical, and
    the character counter keeps reading "0 characters left"."""

    @pytest.mark.p2
    @allure.title(
        "The bucket Name field rejects a 57th character and stays at exactly "
        "56, with no error state"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/artifacts/"
        "ELITEA-1819_bucket-name-field-max-56-characters.md",
        "onetest-ai Test Case link",
    )
    def test_bucket_name_field_rejects_more_than_56_characters(self, page):
        """Drive the case's 9 steps end-to-end against the live system.

        No substitution: the 57th character arrives as a real key event
        (``type()`` and then ``press()``), because the browser's own
        ``maxLength`` enforcement IS the subject — a ``fill()`` would bypass
        it and prove nothing.
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
        bucket_requests = None

        try:
            with allure.step(
                "Step 1 — Navigate to the Artifacts section — the bucket list "
                "renders. Arm a passive capture on any artifacts/buckets "
                "request: this whole case is client-side, and the network is "
                "the only oracle that can prove it"
            ):
                artifacts_page.navigate("/artifacts")
                artifacts_page.wait_for_page_load(timeout=COLD_PAGE_LOAD_TIMEOUT)
                expect(artifacts_page.buckets_heading).to_be_visible(
                    timeout=NAVIGATION_TIMEOUT
                )
                bucket_requests = artifacts_page.capture_requests_matching(
                    "artifacts/buckets"
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
                "Step 3 — Verify the 'New Bucket' form is visible, pre-filled "
                "with its default, and that the Name field ADVERTISES its own "
                "56-character limit — asserting the `maxlength` attribute pins "
                "the enforcement mechanism itself, so a future regression that "
                "drops it fails here at the cause instead of downstream at the "
                "symptom"
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
                expect(artifacts_page.bucket_name_input).to_have_attribute(
                    "maxlength", str(MAX_BUCKET_NAME_LENGTH),
                    timeout=UI_ELEMENT_TIMEOUT,
                )

            with allure.step(
                f"Step 4 — Enter the {MAX_BUCKET_NAME_LENGTH}-character bucket "
                "name — every character is accepted. Focus is deliberately "
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
                "'0 of 56 remaining' (CLARIFICATION #1682, reverse-masking "
                "guard: CharacterCounter.jsx renders "
                "'{remaining} characters left')"
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

            with allure.step(
                f"Step 6 — Attempt one additional character ({EXTRA_CHARACTER!r}) "
                "at the end of the name, delivered as a REAL keystroke — a "
                "fill() would write through the DOM value setter and bypass "
                "the native maxLength constraint that IS this case's subject"
            ):
                artifacts_page.append_to_bucket_name(EXTRA_CHARACTER)

            with allure.step(
                "Step 7 — Verify the additional character was NOT accepted: "
                "the value is byte-identical, still exactly "
                f"{MAX_BUCKET_NAME_LENGTH} characters, and does not end with "
                f"{EXTRA_CHARACTER!r} (length alone would pass even if the "
                "field had silently swapped a character). Asserted for BOTH "
                "key-delivery shapes — type() above and press() here — so a "
                "future implementation that filters only one event path fails"
            ):
                value_after_type = artifacts_page.bucket_name_input.input_value()
                assert value_after_type == bucket_name, (
                    f"After typing a 57th character the Name field must be "
                    f"unchanged: expected {bucket_name!r}, got "
                    f"{value_after_type!r}"
                )
                assert len(value_after_type) == MAX_BUCKET_NAME_LENGTH, (
                    f"Name field must still hold exactly "
                    f"{MAX_BUCKET_NAME_LENGTH} characters, got "
                    f"{len(value_after_type)}"
                )
                assert not value_after_type.endswith(EXTRA_CHARACTER), (
                    f"The rejected character {EXTRA_CHARACTER!r} must not "
                    f"appear at the end of the value, got {value_after_type!r}"
                )

                artifacts_page.bucket_name_input.press(EXTRA_CHARACTER)
                value_after_press = artifacts_page.bucket_name_input.input_value()
                assert value_after_press == bucket_name, (
                    f"A press()-delivered 57th character must be rejected too: "
                    f"expected {bucket_name!r}, got {value_after_press!r}"
                )

            with allure.step(
                "Step 8 — Verify the indicator still reads "
                f"{EXPECTED_COUNTER_TEXT!r} and that the rejection is SILENT: "
                "no aria-invalid, no inline helper text. That is what "
                "distinguishes correct maxLength behaviour from a validation "
                "failure — the case says only 'not accepted'"
            ):
                counter_text_after = (
                    artifacts_page.get_bucket_name_character_counter_text(
                        timeout=UI_ELEMENT_TIMEOUT
                    )
                )
                assert counter_text_after == EXPECTED_COUNTER_TEXT, (
                    f"Expected the counter to still read "
                    f"{EXPECTED_COUNTER_TEXT!r} after the rejected keystroke, "
                    f"got {counter_text_after!r}"
                )
                assert not artifacts_page.is_bucket_name_invalid(
                    timeout=UI_ELEMENT_TIMEOUT
                ), (
                    "The Name field must NOT be flagged aria-invalid — a "
                    "dropped 57th character is silent by design, not a "
                    "validation error"
                )
                expect(artifacts_page.bucket_name_helper_text).to_have_count(
                    0, timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 9 — Verify the bucket name in the Name field is "
                "unchanged (the case brackets the indicator check with two "
                "field assertions — both are kept)"
            ):
                assert (
                    artifacts_page.bucket_name_input.input_value() == bucket_name
                ), (
                    "The Name field's content must be unchanged at the end of "
                    f"the flow: expected {bucket_name!r}, got "
                    f"{artifacts_page.bucket_name_input.input_value()!r}"
                )

            with allure.step(
                "Side-channel checks — the whole boundary is enforced "
                "client-side (zero artifacts/buckets requests) and no console "
                "errors were raised"
            ):
                assert list(bucket_requests) == [], (
                    "This case must fire NO artifacts/buckets request at all — "
                    f"captured: {list(bucket_requests)!r}"
                )
                assert not console_errors, (
                    "Unexpected console errors during the max-length rejection "
                    f"flow: {[m.text for m in console_errors]}"
                )
        finally:
            # The capture helper's own docstring warns that a leaked listener
            # can hang later tests — stop it whatever happened above.
            if bucket_requests is not None:
                bucket_requests.stop()
