"""UI test — Remote MCP create form: validation error on a missing required field.

TMS: ELITEA-1923 (missing Url), ELITEA-1924 (missing Toolkit Name)
AFS: test-specs/mcp/l2_create-remote-mcp-validation-missing-required-field_ELITEA-1923-1924.md
     (FAMILY AFS — both cases are flow-variants of ONE flow, so they are ONE
     parameterized test, one row per TMS case, each row asserting its OWN
     expected values.)

The flow, per row: open the Remote MCP create form, fill exactly ONE of the two
required fields, attempt Save, verify nothing is created and an inline
"Field is required" appears under the field that was left empty, then supply
the missing field and verify the toolkit is created.

Declared substitution: NONE. Every asserted observable is produced by the live
system — the create POST (or its absence), the rendered validation message, and
the detail page's persisted values.

SANCTIONED RED — ELITEA-1924 only (Known defect: #633)
------------------------------------------------------
ELITEA-1924's step 4 (and its Objective, and one of its two Pass criteria)
states the Save button "remains disabled" while only the Url is filled. Live it
is ENABLED: ``shouldDisableSave = isLoading || !formik?.dirty``
(EliteaUI ``src/pages/Toolkits/CreateToolkitToolTabBar.jsx:43-45``) consults
only Formik's dirty flag — never required-field validity, never the name.

That assertion is therefore written as the CASE states it, with
``expect.soft()`` + a ``Known defect: #633`` comment, per
``.agents/testing.md`` § Merge gate -> Analysis-time entry. It is deliberately
NOT rewritten to the live value (that would be reverse-masking — asserting the
product's behaviour instead of the contract under test) and deliberately NOT
dropped (that would be defect-masking). The red is the signal, and it stays
until a human rules whether the product or the case text changes
(see issue #633's 2026-08-24 comment).

The requirement ITSELF is correctly enforced — just at submit time rather than
via the button's disabled state — and that enforcement is asserted HARD below
(no POST fires, the inline error renders, the page does not navigate), so this
row still delivers real coverage of the case's stated intent.
"""

import logging
import re
import uuid
from collections.abc import Callable

import allure
import pytest
from api import ToolkitAPI
from config import settings
from pages.mcp_form_page import McpFormPage
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.toolkits,
    pytest.mark.p2,
    pytest.mark.regression,
    pytest.mark.new,
]

TOOLKIT_URL = "https://mcp.example.com/sse"
VALIDATION_MESSAGE = "Field is required"

# MUI marks an errored FormHelperText with the `Mui-error` class alongside its
# generated `MuiFormHelperText-*` classes; the AFS asserts the class, not just
# the copy, so a helper rendered in the NORMAL (non-error) style with the same
# text could never satisfy this step.
MUI_ERROR_CLASS = re.compile(r"\bMui-error\b")

# Short window in which the create POST must NOT appear. This is an
# absence-of-network-request observable, so it is asserted by expecting the
# wait to TIME OUT — see _assert_no_create_request.
NO_REQUEST_WINDOW = 3_000

# Toolkit Name carries MAX_NAME_LENGTH=32 (EliteaUI src/common/constants.js),
# enforced as inputProps.maxLength and SILENTLY truncating anything longer. A
# 4-hex suffix keeps both of this family's base names inside the cap:
#   autotest_validation_no_url (26) + "_" + 4 = 31
#   autotest_validation_name   (24) + "_" + 4 = 29
NAME_SUFFIX_LEN = 4


def _unique(base: str) -> str:
    name = f"{base}_{uuid.uuid4().hex[:NAME_SUFFIX_LEN]}"
    assert len(name) <= 32, f"Generated name would be silently truncated: {name!r}"
    return name


def _assert_trigger_fires_no_create_request(page, project_id: str, trigger: Callable[[], None]) -> None:
    """Run ``trigger`` and assert the create POST does NOT fire because of it.

    The observable is the ABSENCE of a network request, which Playwright's
    web-first assertions cannot express — so the established in-repo idiom is
    used: wait for the response and treat the timeout as the PASS (cf.
    tests/ui/artifacts/test_artifacts_create_bucket_56char_limit_warning_delete_cancel.py).

    **The trigger runs INSIDE the waiter, and that is load-bearing.**
    ``page.expect_response`` only matches traffic that arrives after its
    ``__enter__``; a create POST that fires on click and resolves before the
    waiter opened would be invisible to it, so a caller that clicks first and
    opens the waiter afterwards asserts nothing at all and passes vacuously.
    Same shape as :meth:`McpFormPage.save_and_wait_for_created`, which wraps
    its own click for the mirror-image reason.

    This is a HARD assertion for both rows — it is not the known defect.
    """
    try:
        with page.expect_response(
            lambda r: f"/tools/prompt_lib/{project_id}" in r.url and r.request.method == "POST",
            timeout=NO_REQUEST_WINDOW,
        ):
            trigger()
    except PlaywrightTimeoutError:
        return  # no create request fired — the expected outcome
    raise AssertionError(
        "A toolkit-creation POST fired even though a required field was empty — "
        "the MCP must NOT be created (ELITEA-1923 step 7 / ELITEA-1924 Pass criteria)"
    )


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1923_create-remote-mcp-validation-error-on-missing-url.md",
    "onetest-ai Test Case link — ELITEA-1923",
)
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1924_create-remote-mcp-validation-error-on-missing-name.md",
    "onetest-ai Test Case link — ELITEA-1924",
)
@pytest.mark.mcp
@pytest.mark.parametrize(
    (
        "name_base",
        "empty_field",
        "helper_locator_name",
        "case_expects_save_disabled_after_partial_fill",
        "known_defect",
    ),
    [
        pytest.param(
            "autotest_validation_no_url",
            "url",
            "url_helper_text",
            # ELITEA-1923 step 4: "Verify Save button becomes enabled
            # (name alone enables it)" — holds live.
            False,
            None,
            id="ELITEA-1923",
        ),
        pytest.param(
            "autotest_validation_name",
            "name",
            "name_helper_text",
            # ELITEA-1924 step 4: "Verify Save button remains disabled
            # (name is required to enable save)" — does NOT hold live.
            True,
            "#633",
            id="ELITEA-1924",
        ),
    ],
)
def test_create_remote_mcp_validation_on_missing_required_field(
    page,
    toolkit_api: ToolkitAPI,
    name_base: str,
    empty_field: str,
    helper_locator_name: str,
    case_expects_save_disabled_after_partial_fill: bool,
    known_defect: str | None,
):
    """Save with one required field empty: error shown, nothing created, then recover."""
    toolkit_name = _unique(name_base)
    project_id = str(settings.elitea_project_id)
    form = McpFormPage(page)
    created_id: int | None = None

    # The two locators are page-object class fields; the row selects WHICH one
    # by name rather than constructing any locator here (locators never live in
    # spec files — .agents/testing.md § Locator policy).
    helper_text = getattr(form, helper_locator_name)
    empty_input = form.url_input if empty_field == "url" else form.name_input
    filled_input = form.name_input if empty_field == "url" else form.url_input
    filled_value = toolkit_name if empty_field == "url" else TOOLKIT_URL
    recovery_value = TOOLKIT_URL if empty_field == "url" else toolkit_name

    # A dirty, unsaved form triggers a native beforeunload confirm dialog if the
    # harness ever navigates away mid-test (e.g. a failure path) — auto-accept
    # it so such a navigation never hangs (AFS § Automation Hints).
    page.on("dialog", lambda dialog: dialog.accept())

    try:
        with allure.step("Step 1 — Navigate to the MCP type picker"):
            form.navigate_to_create()
            assert "/mcps/create" in page.url, f"Expected the MCP type-picker URL, got: {page.url}"

        with allure.step("Step 2 — Select Remote MCP; verify the create form loads"):
            form.select_remote_mcp_type()
            # The case text says /app/mcps/create/mcp; APP_PREFIX is empty on
            # localhost, so a substring assertion is the portable form (same
            # convention as the merged ELITEA-1921/1922 tests).
            assert "/mcps/create/mcp" in page.url, f"Expected the Remote MCP form URL, got: {page.url}"
            expect(form.name_input).to_be_visible()

        with allure.step("Step 3 — Verify Save is disabled on the pristine, untouched form"):
            assert form.is_save_button_disabled(), "Save should be disabled before any field is touched"

        with allure.step(f"Step 4 — Fill the other required field; leave '{empty_field}' empty"):
            if empty_field == "url":
                form.fill_name(filled_value)
            else:
                form.fill_url(filled_value)
            assert filled_input.input_value() == filled_value
            # The emptiness IS this case's precondition — assert it, so a stray
            # autofill or a value leaked from the previous parameterized row
            # cannot silently turn the case into a no-op (AFS Axis 2).
            assert empty_input.input_value() == "", (
                f"The '{empty_field}' field must still be empty before Save is clicked, "
                f"got: {empty_input.input_value()!r}"
            )

        with allure.step(
            f"Step 5 — Verify the Save button state this case expects after only "
            f"the one field is filled: "
            f"{'DISABLED' if case_expects_save_disabled_after_partial_fill else 'ENABLED'}"
            + (
                f" — SANCTIONED RED (Known defect: {known_defect}). The case states "
                "Save REMAINS DISABLED while only the Url is filled; live it is "
                "enabled, because shouldDisableSave = isLoading || !formik?.dirty "
                "consults only Formik's dirty flag, never the Toolkit Name. "
                "Asserted as the CASE states it and collected softly — never "
                "weakened, inverted or skipped"
                if known_defect
                else ""
            )
        ):
            # Each row asserts its OWN expected value. A row tied to an open
            # defect asserts it SOFTLY so the divergence is a visible red
            # instead of a hidden pass.
            # Known defect: #633 (ELITEA-1924 row only).
            save_button_expectation = (
                expect.soft(form.save_button) if known_defect else expect(form.save_button)
            )
            if case_expects_save_disabled_after_partial_fill:
                save_button_expectation.to_be_disabled()
            else:
                save_button_expectation.to_be_enabled()

        with allure.step("Step 6 — Click Save; verify NO toolkit is created"):
            # The click is the TRIGGER passed into the absence assertion, not a
            # separate statement before it: the response waiter must already be
            # open when the click happens, or a POST that fires and resolves
            # first is simply never seen and the assertion passes vacuously.
            _assert_trigger_fires_no_create_request(page, project_id, form.save_button.click)
            assert "/mcps/create/mcp" in page.url, (
                f"Must stay on the create page when a required field is empty, got: {page.url}"
            )
            expect(empty_input).to_have_attribute("aria-invalid", "true")

        with allure.step(f"Step 7 — Verify '{VALIDATION_MESSAGE}' is shown under the '{empty_field}' field"):
            # All three checks the AFS names for this step (§ Test Steps step 7 /
            # Coverage-Map Axis-1 row 6), each catching a different failure:
            #   visible      — the node exists AND is rendered to the user, not
            #                  merely present in the DOM;
            #   exact text   — the Scopes field renders a permanent, unrelated
            #                  helper ("Enter scopes separated by commas or
            #                  spaces") in the same MuiFormHelperText family, so
            #                  a loose/substring check would pass on it;
            #   `Mui-error`  — the helper is shown in the ERROR style, so the
            #                  same copy rendered as ordinary hint text (or the
            #                  error styling silently dropped) still fails.
            expect(helper_text).to_be_visible()
            expect(helper_text).to_have_text(VALIDATION_MESSAGE)
            expect(helper_text).to_have_class(MUI_ERROR_CLASS)

        with allure.step(f"Step 8 — Fill the missing '{empty_field}'; verify the error clears"):
            if empty_field == "url":
                form.fill_url(recovery_value)
            else:
                form.fill_name(recovery_value)
            assert empty_input.input_value() == recovery_value
            # The helper node is UNMOUNTED, not hidden, once the field becomes
            # valid — assert absence by count (canon ruling #511's
            # absence-assertion extension), never not_to_be_visible().
            expect(helper_text).to_have_count(0)
            expect(empty_input).not_to_have_attribute("aria-invalid", "true")
            assert not form.is_save_button_disabled(), (
                "Save should be enabled once both required fields are filled"
            )

        with allure.step("Step 9 — Click Save again; verify 201 + navigation to the detail page"):
            save_response = form.save_and_wait_for_created(project_id)
            created_id = save_response["id"]
            assert isinstance(created_id, int), f"Save response should include a numeric id: {save_response!r}"
            assert f"/mcps/all/{created_id}" in page.url, (
                f"Should navigate to the new MCP's detail page, got: {page.url}"
            )

        with allure.step("Step 10 — Verify the detail page shows the persisted Name and Url"):
            assert toolkit_name in form.get_detail_heading_text()
            assert form.name_input.input_value() == toolkit_name
            # The detail page keeps the schema-driven fields COLLAPSED — no
            # toolkit-field-* element exists until "show more" is clicked
            # (unlike the create form, which renders them inline). Expanding is
            # an ordinary user gesture, not a substitution: the value read
            # below is still the one the product loaded from the server.
            form.expand_configuration_section()
            assert form.url_input.input_value() == TOOLKIT_URL

    finally:
        # Not a case step — cleanup for the persistent server-side toolkit this
        # test creates (AFS § Cleanup). Runs before pytest-playwright re-raises
        # any collected soft-assertion failure, so the ELITEA-1924 row cleans up
        # exactly like the green one.
        if created_id is not None:
            try:
                toolkit_api.delete_toolkit(created_id)
            except Exception:
                logger.warning("Failed to delete MCP toolkit id=%s during cleanup", created_id, exc_info=True)
