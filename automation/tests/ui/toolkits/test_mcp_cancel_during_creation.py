"""UI test — Remote MCP cancel during creation (ELITEA-1960).

Fills the Remote MCP create form, clicks Cancel, confirms the warning dialog
with Discard, and verifies the user leaves the creation form with nothing
created — in the UI list, over the network, and via an independent API read.

**Cancel is a two-step gesture.** The Cancel click alone cancels nothing: it
only opens the confirmation dialog (``CreateToolkitToolTabBar.jsx`` ->
``setOpenAlert(true)``). Step 4 therefore asserts the form is still mounted
and still holds both values, so a regression that cancelled immediately could
not pass the later steps by accident.

**The URL is deliberately not asserted in step 7, in either direction.** The
case's step title says "navigation goes back to MCP create page", but no
``navigate()`` exists anywhere in the cancel path — ``onClearEditTool()`` is
pure component state, so the create form unmounts and the type picker
re-renders while the URL stays ``/mcps/create/mcp``. The case's own *expected
result* ("user is navigated away from the creation form") holds exactly; only
the step title implies a route change. That is case-text imprecision, not a
product defect — filed as CLARIFICATION
EliteaAI/elitea-testing-public#1747 — so this test asserts the LIVE contract:
every create-form handle unmounts AND the type picker is back.

**The "nothing was created" oracle is the passive request observer, not an
API read.** ``ToolkitAPI.list_all_toolkits()`` is a CONFIRMED-BROKEN discovery
path on this environment — ``GET tools/prompt_lib/{project}`` answers
``{"rows": [], "total": 0}`` regardless of params or auth method, re-verified
2026-08-24, and documented in
``.agents/memory/test-automation-engineer/mcp_pipeline_node_toolkit_tool_quirks.md``
plus four merged MCP siblings. Any absence assertion phrased against it is
VACUOUS — it passes whether or not the toolkit exists — so this spec uses none.
The server-side oracle is instead a PASSIVE ``page.on("request")`` observer
proving no mutating toolkit request ever fired, which is strictly stronger:
it also covers a create that succeeded but never reached the list view. Every
absence assertion here is preceded by a presence check proving its channel can
actually see MCPs (see the pre-flight guard and step 8).

No substitutions (AFS § Fidelity Declaration): both fields are filled through
the real inputs, Cancel and Discard are real clicks on the product's own
controls, and the oracles are observation-only. No ``page.route``, no
fabricated response, no injected state, no API-seeded stand-in for a UI step.

Spec: test-specs/mcp/l2_remote-mcp-cancel-during-creation_ELITEA-1960.md
"""

import logging

import allure
import pytest
from pages.mcp_form_page import McpFormPage
from pages.mcp_list_page import McpListPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.toolkits,
    pytest.mark.mcp,
    pytest.mark.p2,
    pytest.mark.regression,
]

# Verbatim from the case's Test Data table. Deliberately NOT uuid-suffixed:
# the whole point is that this name never reaches the server, and a random
# suffix would make step 8's "does not appear" assertion trivially true for
# the wrong reason. The pre-flight guard below makes the fixed literal safe.
TOOLKIT_NAME = "autotest_cancelled"
TOOLKIT_URL = "https://mcp.example.com/sse"

CREATE_FORM_URL_FRAGMENT = "/mcps/create/mcp"
TYPE_PICKER_HEADING = "Choose the MCP type"
CANCEL_CONFIRM_MESSAGE = "Are you sure you want to cancel creation of this toolkit?"

UI_ELEMENT_TIMEOUT = 10_000


def _is_known_656_warning(msg) -> bool:
    """React dev-mode 'unique key prop' error the MCP type picker emits on every
    mount — CategorySection.jsx via ToolkitTypeSelector.jsx, already tracked as
    EliteaAI/elitea-testing-public#656.

    Unlike the neighbouring MCP specs, this flow CANNOT scope the listener away
    from the picker: returning to the picker IS step 7's observable, and the
    picker mounts twice (entry, and again after the cancel). Filtered by exact
    message match rather than disabling the assertion, so a genuinely new error
    in this flow still fails the test.
    """
    # Known defect: EliteaAI/elitea-testing-public#656
    return 'unique "key" prop' in msg.text


def _is_dev_server_noise(msg) -> bool:
    """socket.io polling failures against the DEV backend (CORS / 502 / 503).

    A standing localhost-dev-server-vs-DEV-backend environment characteristic
    (same ``_DEV_SERVER_NOISE`` filter the support-assistant specs use), not
    anything this flow produces.
    """
    return "/socket.io/" in msg.text or "@vite/client" in msg.text


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/mcp/ELITEA-1960_remote-mcp-cancel-during-creation.md",
    "onetest-ai Test Case link",
)
@pytest.mark.mcp
class TestMcpCancelDuringCreation:
    """Remote MCP create form: Cancel -> confirmation dialog -> Discard creates nothing."""

    def test_cancel_during_creation_creates_nothing(self, page):
        """Cancelling MCP creation warns, returns to the type picker, and creates no MCP."""
        form = McpFormPage(page)
        list_page = McpListPage(page)

        with allure.step(
            "Pre-flight guard — no MCP named 'autotest_cancelled' may pre-exist"
        ):
            # Step 8's observable is ABSENCE, so a leftover from an aborted
            # earlier run would make it fail for the wrong reason. Fail fast
            # with a clear message instead of producing a misleading result.
            # Deliberately NOT auto-deleted: a real leftover IS the bug this
            # case exists to catch, and deleting it would erase the evidence.
            #
            # Discovery runs through the MCP LIST VIEW, not the API: the
            # toolkit listing endpoint always answers an empty list here (see
            # the module docstring), which would make this guard vacuous. Same
            # UI-based discovery the sibling delete spec uses
            # (``test_mcp_delete_remote._delete_stale_mcp_if_present``).
            list_page.navigate()
            preflight_unfiltered = list_page.get_card_count()
            # Non-vacuity check FIRST: an absence result is only evidence if
            # the channel can see MCPs at all. Zero cards would mean the list
            # failed to render, and every "not present" below would be free.
            assert preflight_unfiltered > 0, (
                "The MCP list rendered zero cards, so the pre-existence guard below "
                "would be vacuous — the project needs at least one MCP (AFS § Test Data)"
            )
            list_page.search(TOOLKIT_NAME)
            # No clear_search() — see the note in step 8 (defect #1734/#585).
            # Step 1 navigates to the create page explicitly, so the filtered
            # list state is not carried into the flow.
            pre_existing = list_page.get_card_names()
            assert not pre_existing, (
                f"Environment is dirty: an MCP named {TOOLKIT_NAME!r} already exists "
                f"({pre_existing}). Either a previous run of this case genuinely created "
                "one (the defect this case catches) or it was left behind by an aborted "
                "run — investigate, do not auto-delete."
            )

        # Console-error side channel (AFS step 8e / the case's Pass criterion
        # "All steps complete without errors"), registered before step 1 so it
        # spans the whole flow. Two known, unrelated signatures are excluded by
        # exact message match — see the helpers above.
        console_errors: list = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg)
            if msg.type == "error"
            and not _is_known_656_warning(msg)
            and not _is_dev_server_noise(msg)
            else None,
        )

        # PASSIVE request observer (AFS step 8b / § Fidelity Declaration):
        # observation only, no interception, no fulfilment. A UI-list absence
        # alone does not prove nothing was created — a created-then-hidden
        # entity would read the same — so the server-side oracle is that no
        # mutating toolkit request ever fired.
        mutating_toolkit_requests: list = []
        page.on(
            "request",
            lambda req: mutating_toolkit_requests.append(f"{req.method} {req.url}")
            if req.method != "GET" and "prompt_lib" in req.url
            else None,
        )

        with allure.step(
            "Step 1 — Navigate to the MCP creation page and select the Remote MCP type"
        ):
            # The type card mounts asynchronously after the goto (up to ~3.5s);
            # navigate_to_create() owns that wait, never a bare immediate read.
            form.navigate_to_create()
            form.select_remote_mcp_type()
            assert CREATE_FORM_URL_FRAGMENT in page.url, (
                f"Selecting Remote MCP should land on {CREATE_FORM_URL_FRAGMENT!r}, "
                f"got {page.url}"
            )
            expect(form.name_input).to_be_visible()
            expect(form.url_input).to_be_visible()

        with allure.step("Step 2 — Fill 'Toolkit Name *' with 'autotest_cancelled'"):
            form.fill_name(TOOLKIT_NAME)
            expect(form.name_input).to_have_value(TOOLKIT_NAME)

        with allure.step("Step 3 — Fill 'Url *' with the Remote MCP endpoint"):
            form.fill_url(TOOLKIT_URL)
            expect(form.url_input).to_have_value(TOOLKIT_URL)

        with allure.step(
            "Step 3b — Verify the Cancel button is enabled and labelled 'Cancel' "
            "before it is clicked"
        ):
            # Cancel is the control under test; proving it was actionable (and
            # that no dialog was already open) makes step 5's dialog
            # attributable to the click rather than to a pre-existing state.
            expect(form.create_cancel_button).to_be_enabled()
            expect(form.create_cancel_button).to_have_text("Cancel")
            expect(form.cancel_confirm_dialog).to_have_count(0)

        with allure.step("Step 4 — Click 'Cancel' (instead of Save)"):
            form.click_cancel_creation()

        with allure.step(
            "Step 4b — Verify Cancel alone cancelled nothing: the form is still "
            "mounted and still holds both values"
        ):
            # Pins the product's two-step gesture. Without this, a regression
            # that cancelled immediately (skipping the dialog) could still pass
            # steps 5-8 if the dialog happened to render afterwards.
            expect(form.name_input).to_have_value(TOOLKIT_NAME)
            expect(form.url_input).to_have_value(TOOLKIT_URL)
            expect(form.save_button).to_be_visible()

        with allure.step("Step 5 — Verify the warning confirmation dialog appears"):
            expect(form.cancel_confirm_dialog).to_be_visible()
            # The testid lands on the MUI Dialog ROOT, so its text is
            # "Warning" + message + both button labels concatenated — `in`,
            # never `==`.
            message = form.get_cancel_confirm_message()
            assert CANCEL_CONFIRM_MESSAGE in message, (
                f"The cancel-confirmation dialog should ask {CANCEL_CONFIRM_MESSAGE!r}, "
                f"got {message!r}"
            )
            assert "Warning" in message, (
                f"The dialog should carry the 'Warning' title, got {message!r}"
            )
            expect(form.cancel_confirm_button).to_have_text("Discard")

        with allure.step("Step 6 — Click 'Discard' to confirm cancellation"):
            form.confirm_cancel_creation()
            # The dialog is REMOVED from the DOM, not hidden.
            expect(form.cancel_confirm_dialog).to_have_count(0)

        with allure.step(
            "Step 7 — Verify the user is navigated away from the creation form "
            "(the type picker is back; the URL deliberately unasserted — #1747)"
        ):
            # to_have_count(0), not not_to_be_visible(): the create-form nodes
            # are removed from the DOM.
            expect(form.name_input).to_have_count(0)
            expect(form.description_input).to_have_count(0)
            expect(form.url_input).to_have_count(0)
            expect(form.save_button).to_have_count(0)
            expect(form.create_cancel_button).to_have_count(0)
            # The positive half: the type picker actually re-rendered.
            expect(form.type_picker_heading).to_have_text(TYPE_PICKER_HEADING)
            expect(form.remote_mcp_type_card).to_be_visible()

        with allure.step(
            "Step 8 — Verify 'autotest_cancelled' does NOT appear in the MCP list"
        ):
            list_page.navigate()
            # Guards against the vacuous pass where the list failed to load at
            # all and therefore *everything* is "absent".
            count_unfiltered = list_page.get_card_count()
            assert count_unfiltered > 0, (
                "The MCP list rendered zero cards, so the absence assertion below would "
                "be vacuous — the project needs at least one MCP (AFS § Test Data)"
            )
            list_page.search(TOOLKIT_NAME)
            # NOTE: no clear_search() afterwards — clicking Clear while the
            # zero-match empty state shows navigates away to /mcps/create
            # (known defect EliteaAI/elitea-testing-public#1734). The test has
            # no reason to clear.
            assert list_page.get_card_count() == 0, (
                f"Searching for {TOOLKIT_NAME!r} should return no cards after cancellation, "
                f"got {list_page.get_card_names()}"
            )
            expect(list_page.empty_state_title).to_be_visible()

        with allure.step(
            "Step 8b — Verify no mutating toolkit request fired anywhere in the flow"
        ):
            # The independent, non-DOM ground truth for "nothing was created" —
            # it also covers a create that succeeded but never reached the list
            # view, which is why no API-listing assertion is needed (and why
            # none would be honest here — see the module docstring).
            assert not mutating_toolkit_requests, (
                "Cancelling creation must not send any create/update request, but these "
                f"fired: {mutating_toolkit_requests}"
            )

        with allure.step("Step 8e — Verify no unexpected console errors across the flow"):
            assert not console_errors, (
                "Unexpected console errors beyond the pre-existing #656 React `key` "
                "warning and socket.io dev-server noise, got: "
                f"{[m.text for m in console_errors]}"
            )
